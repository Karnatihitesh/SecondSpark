import uuid
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from app.models.user import db, User
from app.models.project import Project, ProjectImage, ProjectDocument, SavedProject, RepairRequest, ProjectMilestone, ProgressUpdate
from app.models.review import Review
from app.models.category import Category
from app.services.auth_service import get_current_user, login_required, slugify
from app.services.project_service import build_project_query, save_uploaded_file
from app.services.notification_service import create_notification
from app.services.recommendation_service import recommend_repairmen_for_project

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

    # Automatic Repairman Recommendations
    rec_data = recommend_repairmen_for_project(project, limit=4)
    recommended_repairmen = rec_data.get('recommendations', [])
    is_fallback_recommendations = rec_data.get('is_fallback', False)

    # Active repair request states
    active_repair_request = None
    user_incoming_request = None
    if user:
        if user.id == project.user_id:
            active_repair_request = RepairRequest.query.filter_by(
                project_id=project.id,
                customer_id=user.id,
                status='Pending'
            ).first()
        else:
            user_incoming_request = RepairRequest.query.filter_by(
                project_id=project.id,
                repairman_id=user.id,
                status='Pending'
            ).first()

    # Milestones & Progress
    milestones = project.milestones.all()
    progress_updates = project.progress_updates.all()

    # Review readiness: Strictly only after 100% and Completed status for project owner
    can_review = False
    has_reviewed = False
    if user:
        existing_review = Review.query.filter_by(project_id=project.id, reviewer_id=user.id).first()
        has_reviewed = existing_review is not None
        if (project.status == 'Completed' and project.current_progress == 100 and
            user.id == project.user_id and project.assigned_repairman_id is not None and not has_reviewed):
            can_review = True

    return render_template(
        'project_details.html',
        project=project,
        is_saved=is_saved,
        similar_projects=similar_projects,
        recommended_repairmen=recommended_repairmen,
        is_fallback_recommendations=is_fallback_recommendations,
        active_repair_request=active_repair_request,
        user_incoming_request=user_incoming_request,
        milestones=milestones,
        progress_updates=progress_updates,
        can_review=can_review,
        has_reviewed=has_reviewed
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


def init_default_milestones(project):
    """Initialize a standard 4-stage verified milestone progression for an assigned build."""
    if project.milestones.count() > 0:
        return
    defaults = [
        ("Milestone 1: Diagnostics & Component Verification", "Analyze stalled build, inspect circuit/code faults, and verify required components.", 25, 1),
        ("Milestone 2: Core Engineering & Circuit Fixes", "Resolve fundamental bottlenecks, solder wiring, and implement core drivers/logic.", 50, 2),
        ("Milestone 3: System Integration & Stress Testing", "Assemble complete build, execute live test benches, and tune operational parameters.", 80, 3),
        ("Milestone 4: Final Quality Verification & Handover", "Complete functional sign-off, capture demo evidence, and package documentation for handover.", 100, 4)
    ]
    for title, desc, target, order in defaults:
        m = ProjectMilestone(
            project_id=project.id,
            title=title,
            description=desc,
            target_percentage=target,
            order=order,
            status='In Progress' if order == 1 else 'Pending'
        )
        db.session.add(m)
    db.session.commit()


@projects_bp.route('/<int:id>/request-repair', methods=['POST'])
@login_required
def request_repair(id):
    """Customer submits a direct repair request to a recommended or selected repairman."""
    project = db.session.get(Project, id)
    if not project:
        abort(404)

    user = get_current_user()
    if project.user_id != user.id:
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'Only the project owner can send repair requests.'}), 403
        flash('Only the project owner can send repair requests.', 'danger')
        return redirect(url_for('projects.details', id=project.id))

    if project.status in ['In Progress', 'Completed', 'Closed']:
        msg = f'This project is already {project.status.lower()} and cannot accept new repair requests.'
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': msg}), 400
        flash(msg, 'warning')
        return redirect(url_for('projects.details', id=project.id))

    repairman_id = request.form.get('repairman_id', type=int)
    if not repairman_id and request.is_json:
        repairman_id = request.json.get('repairman_id')

    if not repairman_id:
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'No repairman selected.'}), 400
        flash('Please select a valid repairman.', 'danger')
        return redirect(url_for('projects.details', id=project.id))

    if repairman_id == user.id:
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'You cannot send a repair request to yourself.'}), 400
        flash('You cannot request yourself for project repair.', 'warning')
        return redirect(url_for('projects.details', id=project.id))

    repairman = db.session.get(User, repairman_id)
    if not repairman or not repairman.is_active:
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'Selected repairman is inactive or not found.'}), 404
        flash('Selected repairman is not available.', 'danger')
        return redirect(url_for('projects.details', id=project.id))

    message = request.form.get('message', '').strip()
    if not message and request.is_json:
        message = request.json.get('message', '').strip()

    # Check for existing pending request
    existing = RepairRequest.query.filter_by(
        project_id=project.id,
        repairman_id=repairman.id,
        status='Pending'
    ).first()

    if existing:
        msg = f'A repair request is already pending for {repairman.full_name}.'
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': msg}), 200
        flash(msg, 'info')
        return redirect(url_for('projects.details', id=project.id))

    try:
        req_obj = RepairRequest(
            project_id=project.id,
            customer_id=user.id,
            repairman_id=repairman.id,
            message=message or f"Hello {repairman.full_name.split(' ')[0]}, I would like to request your assistance and technical expertise to complete this build.",
            status='Pending'
        )
        db.session.add(req_obj)
        project.status = 'Awaiting Repairman'
        db.session.commit()

        # Send in-app notification and email
        create_notification(
            user_id=repairman.id,
            notif_type='offer',
            title='New Repair Request Received',
            message=f'{user.full_name} has requested your expertise to repair "{project.title}".',
            link=url_for('projects.details', id=project.id)
        )

        msg = f'Repair request sent to {repairman.full_name}! You will be notified once they respond.'
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': msg, 'request_id': req_obj.id})
        flash(msg, 'success')
    except Exception as e:
        db.session.rollback()
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'Could not create repair request.'}), 500
        flash('Could not send repair request. Please try again.', 'danger')

    return redirect(url_for('projects.details', id=project.id))


@projects_bp.route('/requests/<int:request_id>/respond', methods=['POST'])
@login_required
def respond_repair_request(request_id):
    """Repairman accepts or rejects an incoming project repair request."""
    user = get_current_user()
    req_obj = db.session.get(RepairRequest, request_id)
    if not req_obj:
        abort(404)

    if req_obj.repairman_id != user.id:
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'Unauthorized to respond to this request.'}), 403
        abort(403)

    if req_obj.status != 'Pending':
        msg = f'This request has already been {req_obj.status.lower()}.'
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': msg}), 400
        flash(msg, 'warning')
        return redirect(url_for('projects.details', id=req_obj.project_id))

    action = request.form.get('action', '').strip().lower()
    if not action and request.is_json:
        action = request.json.get('action', '').strip().lower()

    project = req_obj.project

    if action == 'accept':
        req_obj.status = 'Accepted'
        req_obj.responded_at = datetime.utcnow()
        project.assigned_repairman_id = user.id
        project.status = 'In Progress'
        project.current_progress = 0

        # Initialize standard milestones if none configured
        init_default_milestones(project)

        # Cancel any other pending requests for this project
        RepairRequest.query.filter(
            RepairRequest.project_id == project.id,
            RepairRequest.id != req_obj.id,
            RepairRequest.status == 'Pending'
        ).update({'status': 'Cancelled', 'responded_at': datetime.utcnow()})

        db.session.commit()

        # Notify project customer
        create_notification(
            user_id=project.user_id,
            notif_type='status_change',
            title='Repair Request Accepted! ⚡',
            message=f'{user.full_name} accepted your repair request for "{project.title}". The project is now In Progress!',
            link=url_for('projects.details', id=project.id)
        )

        msg = f'You have successfully accepted the repair request for "{project.title}"! The project is now In Progress.'
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': msg, 'status': 'In Progress'})
        flash(msg, 'success')

    elif action == 'reject':
        req_obj.status = 'Rejected'
        req_obj.responded_at = datetime.utcnow()

        # Check if project has other pending requests or reset to Open
        other_pending = RepairRequest.query.filter_by(project_id=project.id, status='Pending').first()
        if not other_pending and project.status == 'Awaiting Repairman':
            project.status = 'Open'

        db.session.commit()

        create_notification(
            user_id=project.user_id,
            notif_type='status_change',
            title='Repair Request Declined',
            message=f'{user.full_name} was unable to take on "{project.title}". You can browse and select another recommended maker.',
            link=url_for('projects.details', id=project.id)
        )

        msg = f'You declined the repair request for "{project.title}".'
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': msg, 'status': project.status})
        flash(msg, 'info')
    else:
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'Invalid action. Must be accept or reject.'}), 400
        flash('Invalid response action.', 'danger')

    return redirect(url_for('projects.details', id=project.id))


@projects_bp.route('/<int:id>/progress/submit', methods=['POST'])
@login_required
def submit_progress_update(id):
    """
    Assigned repairman submits a progress update proposal.
    Strict Gate: Submitted progress enters 'Pending' status and does NOT
    modify official project progress until approved by customer.
    """
    project = db.session.get(Project, id)
    if not project:
        abort(404)

    user = get_current_user()
    if project.assigned_repairman_id != user.id:
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'Only the assigned repairman can submit progress updates.'}), 403
        flash('Only the assigned repairman can submit progress updates for this project.', 'danger')
        return redirect(url_for('projects.details', id=project.id))

    if project.status == 'Completed':
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'This project is already completed.'}), 400
        flash('This project has already reached 100% completion.', 'info')
        return redirect(url_for('projects.details', id=project.id))

    # Parse inputs
    submitted_pct = request.form.get('submitted_progress', type=int)
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    technologies = request.form.get('technologies_used', '').strip()
    next_step = request.form.get('next_step', '').strip()
    milestone_id = request.form.get('milestone_id', type=int)

    if submitted_pct is None and request.is_json:
        submitted_pct = request.json.get('submitted_progress')
        title = request.json.get('title', '').strip()
        description = request.json.get('description', '').strip()
        technologies = request.json.get('technologies_used', '').strip()
        next_step = request.json.get('next_step', '').strip()
        milestone_id = request.json.get('milestone_id')

    # Strict Validation
    if submitted_pct is None or submitted_pct < project.current_progress:
        err = f'Submitted progress ({submitted_pct}%) cannot be less than currently approved progress ({project.current_progress}%).'
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': err}), 400
        flash(err, 'danger')
        return redirect(url_for('projects.details', id=project.id))

    if submitted_pct > 100:
        err = 'Progress cannot exceed 100%.'
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': err}), 400
        flash(err, 'danger')
        return redirect(url_for('projects.details', id=project.id))

    if not title or not description:
        err = 'Please provide an update title and description of work completed.'
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': err}), 400
        flash(err, 'danger')
        return redirect(url_for('projects.details', id=project.id))

    # Evidence attachment if present
    evidence_url = None
    if 'evidence' in request.files:
        file = request.files['evidence']
        if file and file.filename:
            evidence_url = save_uploaded_file(file, subfolder='evidence', is_image=True)

    try:
        update_obj = ProgressUpdate(
            project_id=project.id,
            repairman_id=user.id,
            milestone_id=milestone_id if milestone_id else (project.active_milestone.id if project.active_milestone else None),
            previous_progress=project.current_progress,
            submitted_progress=submitted_pct,
            title=title,
            description=description,
            technologies_used=technologies,
            next_step=next_step,
            evidence_url=evidence_url,
            status='Pending'
        )
        db.session.add(update_obj)

        # Update project status to indicate approval is needed; DO NOT change current_progress!
        project.status = 'Awaiting Customer Approval'
        db.session.commit()

        # Notify project customer
        create_notification(
            user_id=project.user_id,
            notif_type='status_change',
            title='Progress Update Awaiting Approval',
            message=f'{user.full_name} submitted a progress update ({submitted_pct}%) for "{project.title}". Please review and verify the deliverables.',
            link=url_for('projects.details', id=project.id)
        )

        msg = f'Progress update ({submitted_pct}%) submitted successfully! Awaiting review and approval by the customer.'
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': msg, 'update': update_obj.to_dict()})
        flash(msg, 'success')
    except Exception as e:
        db.session.rollback()
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'Failed to save progress update.'}), 500
        flash('Could not record progress update. Please try again.', 'danger')

    return redirect(url_for('projects.details', id=project.id))


@projects_bp.route('/<int:id>/progress/<int:update_id>/approve', methods=['POST'])
@login_required
def approve_progress_update(id, update_id):
    """
    Strict Customer Approval Gate:
    Only the project owner/customer can approve submitted progress.
    Once approved, the official project progress increases to the submitted level.
    """
    project = db.session.get(Project, id)
    if not project:
        abort(404)

    user = get_current_user()
    if project.user_id != user.id:
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'Unauthorized. Only the project customer can approve progress.'}), 403
        flash('Unauthorized. Only the project customer can approve progress.', 'danger')
        return redirect(url_for('projects.details', id=project.id))

    update_obj = db.session.get(ProgressUpdate, update_id)
    if not update_obj or update_obj.project_id != project.id:
        abort(404)

    if update_obj.status != 'Pending':
        err = f'This update has already been {update_obj.status.lower()}.'
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': err}), 400
        flash(err, 'warning')
        return redirect(url_for('projects.details', id=project.id))

    try:
        # 1. Update official progress
        project.current_progress = update_obj.submitted_progress
        update_obj.status = 'Approved'
        update_obj.reviewed_at = datetime.utcnow()

        # 2. Update milestone status if target percentage met
        if update_obj.milestone:
            if project.current_progress >= update_obj.milestone.target_percentage:
                update_obj.milestone.status = 'Completed'
                update_obj.milestone.completed_at = datetime.utcnow()

        # 3. Check for 100% completion
        if project.current_progress >= 100:
            project.status = 'Completed'
            project.current_progress = 100
            for m in project.milestones:
                m.status = 'Completed'
                if not m.completed_at:
                    m.completed_at = datetime.utcnow()

            db.session.commit()

            # Notify repairman of 100% completion
            create_notification(
                user_id=project.assigned_repairman_id,
                notif_type='status_change',
                title='Build 100% Complete! 🏆',
                message=f'Congratulations! {user.full_name} has approved your final deliverables for "{project.title}". The build is officially Completed!',
                link=url_for('projects.details', id=project.id)
            )

            # Notify customer that review is unlocked
            create_notification(
                user_id=project.user_id,
                notif_type='review',
                title='Leave a Review for your Repairman ⭐',
                message=f'Your project "{project.title}" is complete! Please rate and review your repairman to endorse their craftsmanship.',
                link=url_for('projects.details', id=project.id)
            )

            msg = 'Final progress approved! Project is officially Completed. You can now leave a review for your repairman.'
        else:
            project.status = 'In Progress'
            db.session.commit()

            # Notify repairman
            create_notification(
                user_id=project.assigned_repairman_id,
                notif_type='status_change',
                title='Progress Approved! ✅',
                message=f'{user.full_name} approved your progress update for "{project.title}". Current approved progress: {project.current_progress}%.',
                link=url_for('projects.details', id=project.id)
            )

            msg = f'Progress update ({project.current_progress}%) approved successfully!'

        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': msg, 'current_progress': project.current_progress, 'status': project.status})
        flash(msg, 'success')
    except Exception as e:
        db.session.rollback()
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'Could not process approval.'}), 500
        flash('Could not approve progress update.', 'danger')

    return redirect(url_for('projects.details', id=project.id))


@projects_bp.route('/<int:id>/progress/<int:update_id>/reject', methods=['POST'])
@login_required
def reject_progress_update(id, update_id):
    """
    Customer requests changes on submitted progress.
    Official progress remains unchanged at previous approved percentage.
    """
    project = db.session.get(Project, id)
    if not project:
        abort(404)

    user = get_current_user()
    if project.user_id != user.id:
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'Unauthorized. Only the project customer can request changes.'}), 403
        flash('Unauthorized.', 'danger')
        return redirect(url_for('projects.details', id=project.id))

    update_obj = db.session.get(ProgressUpdate, update_id)
    if not update_obj or update_obj.project_id != project.id:
        abort(404)

    if update_obj.status != 'Pending':
        err = f'This update has already been {update_obj.status.lower()}.'
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': err}), 400
        flash(err, 'warning')
        return redirect(url_for('projects.details', id=project.id))

    comment = request.form.get('customer_comment', '').strip()
    if not comment and request.is_json:
        comment = request.json.get('customer_comment', '').strip()

    if not comment:
        err = 'Please provide specific feedback/reason for requesting changes.'
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': err}), 400
        flash(err, 'danger')
        return redirect(url_for('projects.details', id=project.id))

    try:
        update_obj.status = 'Revision Required'
        update_obj.customer_comment = comment
        update_obj.reviewed_at = datetime.utcnow()

        # Official progress stays untouched!
        project.status = 'In Progress'
        db.session.commit()

        # Notify repairman with feedback
        create_notification(
            user_id=project.assigned_repairman_id,
            notif_type='status_change',
            title='Revision Requested on Progress Update',
            message=f'{user.full_name} requested changes on your progress update for "{project.title}": "{comment[:120]}"',
            link=url_for('projects.details', id=project.id)
        )

        msg = 'Revision request and feedback submitted to your repairman. Official progress remains unchanged.'
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': msg, 'current_progress': project.current_progress})
        flash(msg, 'info')
    except Exception as e:
        db.session.rollback()
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'Could not process rejection.'}), 500
        flash('Could not record feedback.', 'danger')

    return redirect(url_for('projects.details', id=project.id))


@projects_bp.route('/<int:id>/progress-history')
def progress_history(id):
    """Retrieve full progress timeline and audit trail for a project."""
    project = db.session.get(Project, id)
    if not project:
        return jsonify({'success': False, 'error': 'Project not found'}), 404

    updates = [u.to_dict() for u in project.progress_updates.all()]
    milestones = [m.to_dict() for m in project.milestones.all()]

    return jsonify({
        'success': True,
        'project_id': project.id,
        'current_progress': project.current_progress,
        'status': project.status,
        'updates': updates,
        'milestones': milestones
    })

