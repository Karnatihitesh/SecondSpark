from flask import Blueprint, render_template, redirect, url_for, flash, request
from app.models.user import db, User, UserRole
from app.models.project import Project, SavedProject, RepairRequest
from app.models.message import Conversation, Message
from app.models.notification import Notification
from app.models.review import Review
from app.models.category import Category
from app.services.auth_service import get_current_user, login_required, customer_required, technician_required
from app.services.recommendation_service import recommend_repairmen_for_project, recommend_projects_for_technician

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')


@dashboard_bp.route('')
@dashboard_bp.route('/')
@login_required
def index():
    """Primary dashboard entrypoint. Centralizes routing to user's strict role dashboard."""
    user = get_current_user()
    if user.is_admin:
        return redirect(url_for('admin.dashboard'))
    elif user.is_technician:
        return redirect(url_for('dashboard.technician_dashboard'))
    return redirect(url_for('dashboard.customer_dashboard'))


@dashboard_bp.route('/customer/dashboard')
@dashboard_bp.route('/customer')
@dashboard_bp.route('/customer/')
@customer_required
def customer_dashboard():
    """CUSTOMER DASHBOARD: Shows customer's uploaded builds, views, repair status, and milestones."""
    user = get_current_user()
    if user.is_technician:
        return redirect(url_for('dashboard.technician_dashboard'))
    if user.is_admin:
        return redirect(url_for('admin.dashboard'))

    my_projects = user.projects.order_by(Project.created_at.desc()).all()
    total_projects = len(my_projects)
    active_projects = [p for p in my_projects if p.status in ['Open', 'Help Needed', 'In Discussion', 'In Progress', 'Awaiting Customer Approval', 'Revision Required']]
    completed_projects = [p for p in my_projects if p.status == 'Completed']
    saved_count = user.saved_projects.count()

    # Total Views calculated dynamically from database
    total_views = sum(p.views_count or 0 for p in my_projects)

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
        'projects_in_repair': len(active_repairs),
        'completed_projects': len(completed_projects),
        'total_views': total_views,
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


@dashboard_bp.route('/technician/dashboard')
@dashboard_bp.route('/technician')
@dashboard_bp.route('/technician/')
@technician_required
def technician_dashboard():
    """TECHNICIAN DASHBOARD: Dedicated workspace for assigned repairs, repair requests, reviews, and skills."""
    user = get_current_user()
    if user.is_customer:
        return redirect(url_for('dashboard.customer_dashboard'))
    if user.is_admin:
        return redirect(url_for('admin.dashboard'))

    # Assigned repairs
    assigned_repairs = user.assigned_projects.order_by(Project.updated_at.desc()).all()
    active_repairs = [p for p in assigned_repairs if p.status in ['Assigned', 'In Progress', 'Awaiting Customer Approval', 'Revision Required']]
    completed_repairs = [p for p in assigned_repairs if p.status == 'Completed']
    pending_approval_repairs = [p for p in assigned_repairs if p.status == 'Awaiting Customer Approval']

    # Incoming repair invitations from customers
    incoming_requests = user.repair_requests_received.filter_by(status='Pending').order_by(RepairRequest.created_at.desc()).all()

    # Recommended Projects matching technician's skills
    rec_results = recommend_projects_for_technician(user, limit=8)
    suitable_projects = rec_results.get('projects', [])

    # All available public customer-uploaded projects
    available_projects = Project.query.filter(
        Project.assigned_repairman_id == None,
        Project.status.in_(['Open', 'Help Needed']),
        Project.user_id != user.id
    ).order_by(Project.created_at.desc()).limit(12).all()

    # Categories for filters
    categories = Category.query.order_by(Category.name.asc()).all()

    # Reviews received from customers
    reviews = user.reviews_received.order_by(Review.created_at.desc()).all()

    # Unread messages count
    unread_messages = Message.query.filter_by(receiver_id=user.id, is_read=False).count()

    # Notifications
    notifications = user.notifications.order_by(Notification.created_at.desc()).limit(5).all()

    stats = {
        'projects_repaired': user.projects_repaired_count,
        'active_repairs': len(active_repairs),
        'completed_repairs': len(completed_repairs),
        'completed_projects': len(completed_repairs),
        'pending_requests': len(incoming_requests),
        'average_rating': user.average_rating,
        'review_count': user.reviews_count,
        'success_rate': user.success_rate,
        'active_repairs_count': len(active_repairs),
        'incoming_requests_count': len(incoming_requests),
        'completed_repairs_count': len(completed_repairs),
        'pending_approvals_count': len(pending_approval_repairs),
        'rating': user.average_rating,
        'reviews_count': user.reviews_count,
        'unread_messages': unread_messages
    }

    return render_template(
        'dashboard_technician.html',
        stats=stats,
        active_repairs=active_repairs,
        incoming_requests=incoming_requests,
        completed_repairs=completed_repairs,
        pending_approval_repairs=pending_approval_repairs,
        suitable_projects=suitable_projects,
        available_projects=available_projects,
        categories=categories,
        reviews=reviews,
        notifications=notifications
    )


# Alias for backward compatibility
technician_workspace = technician_dashboard


@dashboard_bp.route('/my-projects')
@customer_required
def my_projects():
    """Customer My Uploads route. Renders customer dashboard ensuring all stats and empty states load with HTTP 200."""
    return customer_dashboard()


@dashboard_bp.route('/saved')
@dashboard_bp.route('/saved/')
@login_required
def saved_projects():
    user = get_current_user()
    saved = user.saved_projects.order_by(SavedProject.created_at.desc()).all()
    project_objs = [sp.project for sp in saved if sp.project]
    return render_template('saved_projects.html', saved_items=saved, projects=project_objs)

