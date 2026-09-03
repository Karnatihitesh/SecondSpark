import uuid
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from app.models.user import db, User
from app.models.project import Project, ProjectImage, ProjectDocument, SavedProject
from app.models.category import Category
from app.services.auth_service import get_current_user, login_required, slugify
from app.services.project_service import build_project_query, save_uploaded_file
from app.services.notification_service import create_notification

projects_bp = Blueprint('projects', __name__, url_prefix='/projects')


@projects_bp.route('')
@projects_bp.route('/')
@projects_bp.route('/browse')
def browse():
    search = request.args.get('q', '').strip()
    category_slug = request.args.get('category', 'all').strip()
    status = request.args.get('status', 'all').strip()
    min_budget = request.args.get('min_budget', '').strip()
    max_budget = request.args.get('max_budget', '').strip()
    location = request.args.get('location', '').strip()
    skill = request.args.get('skill', '').strip()
    sort = request.args.get('sort', 'newest').strip()
    page = request.args.get('page', 1, type=int)

    query = build_project_query(
        search=search,
        category_slug=category_slug,
        status=status,
        min_budget=min_budget,
        max_budget=max_budget,
        location=location,
        skill=skill,
        sort=sort
    )

    per_page = 9
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    projects = pagination.items

    categories = Category.query.order_by(Category.name.asc()).all()
    user = get_current_user()

    saved_project_ids = set()
    if user:
        saved_project_ids = set(sp.project_id for sp in user.saved_projects.all())

    return render_template(
        'browse_projects.html',
        projects=projects,
        pagination=pagination,
        categories=categories,
        saved_project_ids=saved_project_ids,
        current_filters={
            'q': search,
            'category': category_slug,
            'status': status,
            'min_budget': min_budget,
            'max_budget': max_budget,
            'location': location,
            'skill': skill,
            'sort': sort
        }
    )


@projects_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    user = get_current_user()
    categories = Category.query.order_by(Category.name.asc()).all()

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        category_id = request.form.get('category_id', type=int)
        short_summary = request.form.get('short_summary', '').strip()
        description = request.form.get('description', '').strip()
        current_condition = request.form.get('current_condition', 'Incomplete').strip()
        problems_faults = request.form.get('problems_faults', '').strip()
        help_required = request.form.get('help_required', '').strip()
        required_skills = request.form.get('required_skills', '').strip()
        budget = request.form.get('budget', 0, type=float)
        budget_type = request.form.get('budget_type', 'Fixed').strip()
        location = request.form.get('location', 'Remote').strip()
        deadline = request.form.get('deadline', '').strip()

        if not title or not short_summary or not description or not problems_faults or not help_required or not required_skills:
            flash('Please fill in all required fields.', 'danger')
            return render_template('upload_project.html', categories=categories, form_data=request.form)

        if budget is not None and 0 < budget < 500:
            flash('Minimum repair cost / budget must be at least ₹500 INR (or 0 for open volunteer collaboration).', 'danger')
            return render_template('upload_project.html', categories=categories, form_data=request.form)

        base_slug = slugify(title)
        slug = base_slug
        counter = 1
        while Project.query.filter_by(slug=slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1

        try:
            project = Project(
                user_id=user.id,
                category_id=category_id,
                title=title,
                slug=slug,
                short_summary=short_summary,
                description=description,
                current_condition=current_condition,
                problems_faults=problems_faults,
                help_required=help_required,
                required_skills=required_skills,
                budget=budget,
                budget_type=budget_type,
                location=location,
                deadline=deadline,
                status='Open'
            )
            db.session.add(project)
            db.session.flush()

            images = request.files.getlist('images')
            is_first = True
            for img in images:
                if img and img.filename:
                    url = save_uploaded_file(img, subfolder='projects', is_image=True)
                    if url:
                        p_img = ProjectImage(
                            project_id=project.id,
                            image_url=url,
                            is_primary=is_first
                        )
                        db.session.add(p_img)
                        is_first = False

            documents = request.files.getlist('documents')
            for doc in documents:
                if doc and doc.filename:
                    url = save_uploaded_file(doc, subfolder='projects', is_image=False)
                    if url:
                        p_doc = ProjectDocument(
                            project_id=project.id,
                            file_url=url,
                            filename=doc.filename
                        )
                        db.session.add(p_doc)

            db.session.commit()
            flash('Your project has been posted to SecondSpark! Skilled collaborators can now discover and revive it.', 'success')
            return redirect(url_for('projects.details', id=project.id))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while publishing your project. Please try again.', 'danger')

    return render_template('upload_project.html', categories=categories, form_data={})


@projects_bp.route('/<int:id>')
def details(id):
    project = db.session.get(Project, id)
    if not project:
        abort(404)
    
    project.views_count += 1
    db.session.commit()

    user = get_current_user()
    is_saved = False
    if user:
        is_saved = SavedProject.query.filter_by(user_id=user.id, project_id=project.id).first() is not None

    similar_projects = Project.query.filter(
        Project.category_id == project.category_id,
        Project.id != project.id
    ).limit(3).all()

    return render_template(
        'project_details.html',
        project=project,
        is_saved=is_saved,
        similar_projects=similar_projects
    )


@projects_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    project = db.session.get(Project, id)
    if not project:
        abort(404)
    user = get_current_user()

    if project.user_id != user.id and not user.is_admin:
        abort(403)

    categories = Category.query.order_by(Category.name.asc()).all()

    if request.method == 'POST':
        project.title = request.form.get('title', '').strip()
        project.category_id = request.form.get('category_id', type=int)
        project.short_summary = request.form.get('short_summary', '').strip()
        project.description = request.form.get('description', '').strip()
        project.current_condition = request.form.get('current_condition', 'Incomplete').strip()
        project.problems_faults = request.form.get('problems_faults', '').strip()
        project.help_required = request.form.get('help_required', '').strip()
        project.required_skills = request.form.get('required_skills', '').strip()
        project.budget = request.form.get('budget', 0, type=float)
        project.budget_type = request.form.get('budget_type', 'Fixed').strip()
        project.location = request.form.get('location', 'Remote').strip()
        project.deadline = request.form.get('deadline', '').strip()
        project.status = request.form.get('status', project.status).strip()

        images = request.files.getlist('images')
        for img in images:
            if img and img.filename:
                url = save_uploaded_file(img, subfolder='projects', is_image=True)
                if url:
                    p_img = ProjectImage(project_id=project.id, image_url=url, is_primary=False)
                    db.session.add(p_img)

        try:
            db.session.commit()
            flash('Project details updated successfully.', 'success')
            return redirect(url_for('projects.details', id=project.id))
        except Exception as e:
            db.session.rollback()
            flash('Failed to update project.', 'danger')

    return render_template('edit_project.html', project=project, categories=categories)


@projects_bp.route('/<int:id>/status', methods=['POST'])
@login_required
def update_status(id):
    project = db.session.get(Project, id)
    if not project:
        abort(404)
    user = get_current_user()

    if project.user_id != user.id and not user.is_admin:
        abort(403)

    new_status = request.form.get('status')
    valid_statuses = ['Open', 'Help Needed', 'In Discussion', 'In Progress', 'Completed', 'Closed']
    if new_status in valid_statuses:
        project.status = new_status
        db.session.commit()
        flash(f'Project status updated to "{new_status}".', 'success')
    else:
        flash('Invalid status provided.', 'danger')

    return redirect(request.referrer or url_for('projects.details', id=project.id))


@projects_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    project = db.session.get(Project, id)
    if not project:
        abort(404)
    user = get_current_user()

    if project.user_id != user.id and not user.is_admin:
        abort(403)

    db.session.delete(project)
    db.session.commit()
    flash('Project has been deleted permanently.', 'info')
    return redirect(url_for('dashboard.my_projects'))


@projects_bp.route('/<int:id>/save', methods=['POST'])
@login_required
def toggle_save(id):
    project = db.session.get(Project, id)
    if not project:
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        abort(404)
    user = get_current_user()

    existing = SavedProject.query.filter_by(user_id=user.id, project_id=project.id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        saved = False
        msg = 'Project removed from bookmarks.'
    else:
        sp = SavedProject(user_id=user.id, project_id=project.id)
        db.session.add(sp)
        db.session.commit()
        saved = True
        msg = 'Project saved to bookmarks!'

    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True, 'saved': saved, 'message': msg, 'saves_count': project.saves_count})

    flash(msg, 'success')
    return redirect(request.referrer or url_for('projects.details', id=project.id))
