from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, jsonify
from app.models.user import db, User
from app.models.project import Project, ProjectImage, RepairRequest
from app.models.review import Review
from app.models.category import Category
from app.models.report import Report
from app.models.contact import ContactMessage
from app.models.message import Message
from app.services.auth_service import admin_required, slugify
from app.services.notification_service import create_notification

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('')
@admin_bp.route('/')
@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """ADMIN CONTROL PANEL: Dedicated monitoring, user, technician, project, and review moderation."""
    tab = request.args.get('tab', 'overview')
    role_filter = request.args.get('role', 'all').strip().lower()
    search_query = request.args.get('q', '').strip()
    
    total_users = User.query.count()
    total_customers = User.query.filter(User.role.in_(['customer', 'user'])).count()
    total_technicians = User.query.filter_by(role='technician').count()
    total_projects = Project.query.count()
    published_projects = Project.query.filter(Project.status.in_(['Open', 'Help Needed', 'Published'])).count()
    active_repairs = Project.query.filter(Project.status.in_(['Assigned', 'In Progress', 'Awaiting Customer Approval', 'Revision Required'])).count()
    completed_projects = Project.query.filter_by(status='Completed').count()
    pending_requests = RepairRequest.query.filter_by(status='Pending').count()
    total_reviews = Review.query.count()
    pending_reports = Report.query.filter_by(status='Pending').count()
    total_messages = Message.query.count()
    unread_contacts = ContactMessage.query.filter_by(status='Unread').count()

    stats = {
        'total_users': total_users,
        'total_customers': total_customers,
        'total_technicians': total_technicians,
        'total_projects': total_projects,
        'published_projects': published_projects,
        'active_projects': active_repairs + published_projects,
        'active_repairs': active_repairs,
        'completed_projects': completed_projects,
        'pending_requests': pending_requests,
        'total_reviews': total_reviews,
        'pending_reports': pending_reports,
        'total_messages': total_messages,
        'unread_contacts': unread_contacts
    }

    # Query users with search and filter
    user_query = User.query
    if role_filter == 'customer':
        user_query = user_query.filter(User.role.in_(['customer', 'user']))
    elif role_filter == 'technician':
        user_query = user_query.filter_by(role='technician')
    elif role_filter == 'admin':
        user_query = user_query.filter_by(role='admin')

    if search_query:
        search_fmt = f"%{search_query}%"
        user_query = user_query.filter(
            (User.username.ilike(search_fmt)) |
            (User.email.ilike(search_fmt)) |
            (User.full_name.ilike(search_fmt))
        )

    users = user_query.order_by(User.created_at.desc()).all()
    technicians = User.query.filter_by(role='technician').order_by(User.created_at.desc()).all()
    projects = Project.query.order_by(Project.created_at.desc()).all()
    reviews = Review.query.order_by(Review.created_at.desc()).all()
    reports = Report.query.order_by(Report.created_at.desc()).all()
    categories = Category.query.order_by(Category.name.asc()).all()
    contact_messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()

    return render_template(
        'admin.html',
        stats=stats,
        tab=tab,
        users=users,
        technicians=technicians,
        projects=projects,
        reviews=reviews,
        reports=reports,
        categories=categories,
        contact_messages=contact_messages,
        role_filter=role_filter,
        search_query=search_query
    )


index = dashboard


@admin_bp.route('/users/<int:id>/toggle-status', methods=['POST'])
@admin_required
def toggle_user_status(id):
    user = db.session.get(User, id)
    if not user:
        abort(404)
    user.is_active = not user.is_active
    db.session.commit()
    status_str = "activated" if user.is_active else "suspended"
    flash(f'User "{user.username}" has been {status_str}.', 'info')
    return redirect(url_for('admin.index', tab='users'))


@admin_bp.route('/projects/<int:id>/toggle-feature', methods=['POST'])
@admin_required
def toggle_project_feature(id):
    project = db.session.get(Project, id)
    if not project:
        abort(404)
    project.is_featured = not project.is_featured
    db.session.commit()
    status_str = "featured" if project.is_featured else "unfeatured"
    flash(f'Project "{project.title}" has been {status_str}.', 'success')
    return redirect(url_for('admin.index', tab='projects'))


@admin_bp.route('/projects/<int:id>/delete', methods=['POST'])
@admin_required
def delete_project(id):
    project = db.session.get(Project, id)
    if not project:
        abort(404)
    title = project.title
    db.session.delete(project)
    db.session.commit()
    flash(f'Project "{title}" removed by administrator.', 'warning')
    return redirect(url_for('admin.index', tab='projects'))


@admin_bp.route('/reports/<int:id>/resolve', methods=['POST'])
@admin_required
def resolve_report(id):
    report = db.session.get(Report, id)
    if not report:
        abort(404)
    action = request.form.get('action', 'Resolved')
    admin_notes = request.form.get('admin_notes', '')

    report.status = action
    report.admin_notes = admin_notes
    report.resolved_at = datetime.utcnow()
    db.session.commit()
    flash(f'Report #{report.id} marked as {action}.', 'success')
    return redirect(url_for('admin.index', tab='reports'))


@admin_bp.route('/categories/add', methods=['POST'])
@admin_required
def add_category():
    name = request.form.get('name', '').strip()
    icon = request.form.get('icon', 'fa-cube').strip()
    description = request.form.get('description', '').strip()

    if not name:
        flash('Category name is required.', 'danger')
        return redirect(url_for('admin.index', tab='categories'))

    slug = slugify(name)
    if Category.query.filter_by(slug=slug).first():
        flash('A category with this name already exists.', 'warning')
        return redirect(url_for('admin.index', tab='categories'))

    category = Category(name=name, slug=slug, icon=icon, description=description)
    db.session.add(category)
    db.session.commit()
    flash(f'Category "{name}" created.', 'success')
    return redirect(url_for('admin.index', tab='categories'))


@admin_bp.route('/contacts/<int:id>/mark-read', methods=['POST'])
@admin_required
def mark_contact_read(id):
    contact = db.session.get(ContactMessage, id)
    if not contact:
        abort(404)
    contact.status = 'Read'
    db.session.commit()
    flash('Contact inquiry marked as read.', 'info')
    return redirect(url_for('admin.index', tab='contacts'))


@admin_bp.route('/reviews/<int:id>/delete', methods=['POST'])
@admin_required
def delete_review(id):
    review = db.session.get(Review, id)
    if not review:
        abort(404)
    db.session.delete(review)
    db.session.commit()
    flash('Review permanently removed by administrator.', 'warning')
    return redirect(url_for('admin.dashboard', tab='reviews'))


@admin_bp.route('/users/<int:id>/change-role', methods=['POST'])
@admin_required
def change_user_role(id):
    user = db.session.get(User, id)
    if not user:
        abort(404)
    new_role = request.form.get('role', '').strip().lower()
    if new_role in ['customer', 'technician', 'admin']:
        user.role = new_role
        db.session.commit()
        flash(f'User "{user.username}" role updated to {new_role}.', 'success')
    return redirect(url_for('admin.dashboard', tab='users'))
