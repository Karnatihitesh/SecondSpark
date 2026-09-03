from flask import Blueprint, render_template, redirect, url_for, flash, request
from app.models.user import db, User, UserRole
from app.models.project import Project, SavedProject, RepairRequest
from app.models.message import Conversation, Message
from app.models.notification import Notification
from app.models.review import Review
from app.services.auth_service import get_current_user, login_required, customer_required, technician_required
from app.services.recommendation_service import recommend_repairmen_for_project

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')


@dashboard_bp.route('')
@dashboard_bp.route('/')
@login_required
def index():
    """Primary dashboard entrypoint. Routes user directly to their role-specific workspace."""
    user = get_current_user()
    if user.is_technician:
        return redirect(url_for('dashboard.technician_workspace'))

    # CUSTOMER DASHBOARD
    my_projects = user.projects.order_by(Project.created_at.desc()).all()
    total_projects = len(my_projects)
    active_projects = [p for p in my_projects if p.status in ['Open', 'Help Needed', 'In Discussion', 'In Progress', 'Awaiting Customer Approval', 'Revision Required']]
    completed_projects = [p for p in my_projects if p.status == 'Completed']
    saved_count = user.saved_projects.count()

    # Pending customer approval requests on user's own projects
    pending_approvals = [p for p in my_projects if p.status == 'Awaiting Customer Approval']

    # Active assigned repairs (where a technician is working on customer's project)
    active_repairs = [p for p in my_projects if p.assigned_repairman_id is not None and p.status != 'Completed']

    # Recommended technicians for the customer's most recent open project
    recommended_technicians = []
    open_build = next((p for p in my_projects if p.status in ['Open', 'Help Needed'] and not p.assigned_repairman_id), None)
    if open_build:
        rec_data = recommend_repairmen_for_project(open_build, limit=4)
        recommended_technicians = rec_data.get('recommendations', [])

    # Unread messages count
    unread_messages = Message.query.filter_by(receiver_id=user.id, is_read=False).count()

    # Recent notifications
    notifications = user.notifications.order_by(Notification.created_at.desc()).limit(5).all()

    # Reviews given by this customer
    reviews_given = user.reviews_given.order_by(Review.created_at.desc()).limit(4).all()

    stats = {
        'total_projects': total_projects,
        'active_projects': len(active_projects),
        'completed_projects': len(completed_projects),
        'saved_count': saved_count,
        'unread_messages': unread_messages,
        'pending_approvals_count': len(pending_approvals),
        'active_repairs_count': len(active_repairs)
    }

    return render_template(
        'dashboard.html',
        stats=stats,
        my_projects=my_projects,
        active_projects=active_projects,
        completed_projects=completed_projects,
        pending_approvals=pending_approvals,
        active_repairs=active_repairs,
        recommended_technicians=recommended_technicians,
        featured_project=open_build,
        notifications=notifications,
        reviews_given=reviews_given
    )


@dashboard_bp.route('/technician')
@dashboard_bp.route('/technician/')
@technician_required
def technician_workspace():
    """Dedicated Technician Workspace for managing assigned repairs, incoming requests, and reputation."""
    user = get_current_user()

    # Assigned repairs
    assigned_repairs = user.assigned_projects.order_by(Project.updated_at.desc()).all()
    active_repairs = [p for p in assigned_repairs if p.status in ['Assigned', 'In Progress', 'Awaiting Customer Approval', 'Revision Required']]
    completed_repairs = [p for p in assigned_repairs if p.status == 'Completed']
    pending_approval_repairs = [p for p in assigned_repairs if p.status == 'Awaiting Customer Approval']

    # Incoming repair invitations from customers
    incoming_requests = user.repair_requests_received.filter_by(status='Pending').order_by(RepairRequest.created_at.desc()).all()

    # Find open projects matching technician's skills
    tech_skills = set(s.lower() for s in user.skills_list)
    available_projects_query = Project.query.filter(
        Project.assigned_repairman_id == None,
        Project.status.in_(['Open', 'Help Needed']),
        Project.user_id != user.id
    ).order_by(Project.created_at.desc()).limit(12).all()

    suitable_projects = []
    for p in available_projects_query:
        p_skills = set(s.lower() for s in p.skills_list)
        overlap = len(tech_skills.intersection(p_skills)) if tech_skills and p_skills else 0
        match_pct = int(min(100, max(40, (overlap / max(1, len(p_skills))) * 100))) if overlap > 0 else 45
        suitable_projects.append({'project': p, 'match_pct': match_pct, 'matching_skills': list(tech_skills.intersection(p_skills))})

    # Sort suitable projects by match percentage
    suitable_projects.sort(key=lambda x: x['match_pct'], reverse=True)

    # Reviews received from customers
    reviews = user.reviews_received.order_by(Review.created_at.desc()).all()

    # Unread messages count
    unread_messages = Message.query.filter_by(receiver_id=user.id, is_read=False).count()

    # Notifications
    notifications = user.notifications.order_by(Notification.created_at.desc()).limit(5).all()

    stats = {
        'active_repairs_count': len(active_repairs),
        'incoming_requests_count': len(incoming_requests),
        'completed_repairs_count': len(completed_repairs),
        'pending_approvals_count': len(pending_approval_repairs),
        'rating': user.average_rating,
        'reviews_count': user.reviews_count,
        'success_rate': user.success_rate,
        'unread_messages': unread_messages
    }

    return render_template(
        'dashboard_technician.html',
        stats=stats,
        active_repairs=active_repairs,
        incoming_requests=incoming_requests,
        completed_repairs=completed_repairs,
        pending_approval_repairs=pending_approval_repairs,
        suitable_projects=suitable_projects[:6],
        reviews=reviews,
        notifications=notifications
    )


@dashboard_bp.route('/my-projects')
@customer_required
def my_projects():
    user = get_current_user()
    projects = user.projects.order_by(Project.created_at.desc()).all()
    return render_template('dashboard.html', view_mode='my_projects', my_projects=projects)


@dashboard_bp.route('/saved')
@dashboard_bp.route('/saved/')
@login_required
def saved_projects():
    user = get_current_user()
    saved = user.saved_projects.order_by(SavedProject.created_at.desc()).all()
    project_objs = [sp.project for sp in saved if sp.project]
    return render_template('saved_projects.html', saved_items=saved, projects=project_objs)

