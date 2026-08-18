from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, jsonify
from app.models.user import db, User
from app.models.project import Project, ProjectImage
from app.models.category import Category
from app.models.report import Report
from app.models.contact import ContactMessage
from app.models.message import Message
from app.services.auth_service import admin_required, slugify
from app.services.notification_service import create_notification

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/')
@admin_required
def index():
    tab = request.args.get('tab', 'overview')
    
    total_users = User.query.count()
    total_projects = Project.query.count()
    active_projects = Project.query.filter(Project.status.in_(['Open', 'Help Needed', 'In Discussion', 'In Progress'])).count()
    completed_projects = Project.query.filter_by(status='Completed').count()
    pending_reports = Report.query.filter_by(status='Pending').count()
    total_messages = Message.query.count()
    unread_contacts = ContactMessage.query.filter_by(status='Unread').count()

    stats = {
        'total_users': total_users,
        'total_projects': total_projects,
        'active_projects': active_projects,
        'completed_projects': completed_projects,
        'pending_reports': pending_reports,
        'total_messages': total_messages,
        'unread_contacts': unread_contacts
    }

    users = User.query.order_by(User.created_at.desc()).all()
    projects = Project.query.order_by(Project.created_at.desc()).all()
    reports = Report.query.order_by(Report.created_at.desc()).all()
    categories = Category.query.order_by(Category.name.asc()).all()
    contact_messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()

    return render_template(
        'admin.html',
        stats=stats,
        tab=tab,
        users=users,
        projects=projects,
        reports=reports,
        categories=categories,
        contact_messages=contact_messages
    )


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
