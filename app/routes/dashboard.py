from flask import Blueprint, render_template
from app.models.user import db
from app.models.project import Project, SavedProject, RepairRequest
from app.models.message import Conversation, Message
from app.models.notification import Notification
from app.models.review import Review
from app.services.auth_service import get_current_user, login_required

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')


@dashboard_bp.route('')
@dashboard_bp.route('/')
@login_required
def index():
    user = get_current_user()

    # User project stats (as project owner)
    my_projects = user.projects.order_by(Project.created_at.desc()).all()
    total_projects = len(my_projects)
    active_projects = sum(1 for p in my_projects if p.status in ['Open', 'Help Needed', 'In Discussion', 'In Progress', 'Awaiting Customer Approval', 'Revision Required'])
    completed_projects = sum(1 for p in my_projects if p.status == 'Completed')
    saved_count = user.saved_projects.count()

    # Pending customer approval requests on user's own projects
    pending_approvals = [p for p in my_projects if p.status == 'Awaiting Customer Approval']

    # Repairman stats (as assigned maker / collaborator)
    assigned_repairs = user.assigned_projects.order_by(Project.updated_at.desc()).all()
    active_repairs = [p for p in assigned_repairs if p.status in ['Assigned', 'In Progress', 'Awaiting Customer Approval', 'Revision Required']]
    incoming_requests = user.repair_requests_received.filter_by(status='Pending').order_by(RepairRequest.created_at.desc()).all()

    # Unread messages count
    unread_messages = Message.query.filter_by(receiver_id=user.id, is_read=False).count()

    # Recent conversations
    conversations = Conversation.query.filter(
        (Conversation.user1_id == user.id) | (Conversation.user2_id == user.id)
    ).order_by(Conversation.last_message_at.desc()).limit(5).all()

    # Recent notifications
    notifications = user.notifications.order_by(Notification.created_at.desc()).limit(5).all()

    # Reviews received
    reviews = user.reviews_received.order_by(Review.created_at.desc()).limit(4).all()

    stats = {
        'total_projects': total_projects,
        'active_projects': active_projects,
        'completed_projects': completed_projects,
        'saved_count': saved_count,
        'unread_messages': unread_messages,
        'pending_approvals_count': len(pending_approvals),
        'assigned_repairs_count': len(assigned_repairs),
        'active_repairs_count': len(active_repairs),
        'incoming_requests_count': len(incoming_requests),
        'projects_repaired_count': user.projects_repaired_count,
        'rating': user.average_rating,
        'success_rate': user.success_rate
    }

    return render_template(
        'dashboard.html',
        stats=stats,
        recent_projects=my_projects[:4],
        assigned_repairs=assigned_repairs,
        incoming_requests=incoming_requests,
        pending_approvals=pending_approvals,
        conversations=conversations,
        notifications=notifications,
        reviews=reviews
    )


@dashboard_bp.route('/my-projects')
@login_required
def my_projects():
    user = get_current_user()
    projects = user.projects.order_by(Project.created_at.desc()).all()
    return render_template('dashboard.html', view_mode='my_projects', projects=projects)


@dashboard_bp.route('/saved')
@dashboard_bp.route('/saved/')
@login_required
def saved_projects():
    user = get_current_user()
    saved = user.saved_projects.order_by(SavedProject.created_at.desc()).all()
    project_objs = [sp.project for sp in saved if sp.project]
    return render_template('saved_projects.html', saved_items=saved, projects=project_objs)
