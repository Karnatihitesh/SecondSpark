from flask import Blueprint, render_template
from app.models.user import db
from app.models.project import Project, SavedProject
from app.models.message import Conversation, Message
from app.models.notification import Notification
from app.models.review import Review
from app.services.auth_service import get_current_user, login_required

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')


@dashboard_bp.route('/')
@login_required
def index():
    user = get_current_user()

    # User project stats
    my_projects = user.projects.order_by(Project.created_at.desc()).all()
    total_projects = len(my_projects)
    active_projects = sum(1 for p in my_projects if p.status in ['Open', 'Help Needed', 'In Discussion', 'In Progress'])
    completed_projects = sum(1 for p in my_projects if p.status == 'Completed')
    saved_count = user.saved_projects.count()

    # Unread messages count
    unread_messages = Message.query.filter_by(receiver_id=user.id, is_read=False).count()

    # Recent conversations
    conversations = Conversation.query.filter(
        (Conversation.user1_id == user.id) | (Conversation.user2_id == user.id)
    ).order_by(Conversation.last_message_at.desc()).limit(5).all()

    # Recent notifications
    notifications = user.notifications.order_by(Notification.created_at.desc()).limit(5).all()

    # Reviews received
    reviews = user.reviews_received.order_by(Review.created_at.desc()).limit(3).all()

    stats = {
        'total_projects': total_projects,
        'active_projects': active_projects,
        'completed_projects': completed_projects,
        'saved_count': saved_count,
        'unread_messages': unread_messages
    }

    return render_template(
        'dashboard.html',
        stats=stats,
        recent_projects=my_projects[:4],
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
@login_required
def saved_projects():
    user = get_current_user()
    saved = user.saved_projects.order_by(SavedProject.created_at.desc()).all()
    projects = [sp.project_id for sp in saved]
    project_objs = [sp.project for sp in saved if sp.project]
    return render_template('saved_projects.html', saved_items=saved, projects=project_objs)
