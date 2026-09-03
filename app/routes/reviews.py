from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, jsonify
from app.models.user import db, User
from app.models.project import Project
from app.models.review import Review
from app.services.auth_service import get_current_user, login_required
from app.services.notification_service import create_notification

reviews_bp = Blueprint('reviews', __name__, url_prefix='/reviews')


@reviews_bp.route('')
@reviews_bp.route('/')
def index():
    """Community reviews & success feedback."""
    page = request.args.get('page', 1, type=int)
    rating_filter = request.args.get('rating', type=int)

    query = Review.query.order_by(Review.created_at.desc())
    if rating_filter and 1 <= rating_filter <= 5:
        query = query.filter(Review.rating == rating_filter)

    reviews_pagination = query.paginate(page=page, per_page=12, error_out=False)

    # Review stats
    total_reviews = Review.query.count()
    five_stars = Review.query.filter_by(rating=5).count()
    avg_rating = 5.0
    if total_reviews > 0:
        total_sum = sum(r.rating for r in Review.query.all())
        avg_rating = round(total_sum / total_reviews, 1)

    return render_template(
        'reviews.html',
        reviews=reviews_pagination.items,
        pagination=reviews_pagination,
        total_reviews=total_reviews,
        five_stars=five_stars,
        avg_rating=avg_rating,
        selected_rating=rating_filter
    )


@reviews_bp.route('/create/<int:project_id>', methods=['POST'])
@login_required
def create(project_id):
    current_user = get_current_user()
    project = db.session.get(Project, project_id)
    if not project:
        abort(404)

    # STRICT COMPLETION GATE: Project must be 100% and Completed
    if project.status != 'Completed' or project.current_progress < 100:
        msg = f'Reviews can only be submitted once the project reaches 100% completion and is marked Completed (current approved progress: {project.current_progress}%).'
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': msg}), 400
        flash(msg, 'warning')
        return redirect(url_for('projects.details', id=project.id))

    # Reviewer must be project owner/customer
    if current_user.id != project.user_id:
        msg = 'Only the project owner can submit a review for the assigned repairman.'
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': msg}), 403
        flash(msg, 'danger')
        return redirect(url_for('projects.details', id=project.id))

    # Reviewee must be assigned repairman
    reviewee_id = project.assigned_repairman_id
    if not reviewee_id:
        msg = 'No assigned repairman found for this project.'
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': msg}), 400
        flash(msg, 'warning')
        return redirect(url_for('projects.details', id=project.id))

    if reviewee_id == current_user.id:
        msg = 'You cannot review yourself.'
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': msg}), 400
        flash(msg, 'warning')
        return redirect(url_for('projects.details', id=project.id))

    # Parse rating & sub-criteria
    rating = request.form.get('rating', type=int)
    comment = request.form.get('comment', '').strip()
    quality = request.form.get('quality_rating', type=int, default=5)
    comm = request.form.get('communication_rating', type=int, default=5)
    timeliness = request.form.get('timeliness_rating', type=int, default=5)
    tech = request.form.get('technical_skill_rating', type=int, default=5)

    if request.is_json:
        data = request.get_json() or {}
        rating = data.get('rating', rating)
        comment = data.get('comment', comment).strip() if data.get('comment') else comment
        quality = data.get('quality_rating', quality)
        comm = data.get('communication_rating', comm)
        timeliness = data.get('timeliness_rating', timeliness)
        tech = data.get('technical_skill_rating', tech)

    if not rating or rating < 1 or rating > 5 or not comment:
        msg = 'Please provide a star rating (1-5) and written feedback.'
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': msg}), 400
        flash(msg, 'danger')
        return redirect(url_for('projects.details', id=project.id))

    # Check for duplicate review
    existing = Review.query.filter_by(
        project_id=project.id,
        reviewer_id=current_user.id,
        reviewee_id=reviewee_id
    ).first()

    if existing:
        msg = 'You have already submitted a review for this completed project.'
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': msg}), 400
        flash(msg, 'warning')
        return redirect(url_for('projects.details', id=project.id))

    try:
        review = Review(
            project_id=project.id,
            reviewer_id=current_user.id,
            reviewee_id=reviewee_id,
            rating=rating,
            quality_rating=quality,
            communication_rating=comm,
            timeliness_rating=timeliness,
            technical_skill_rating=tech,
            comment=comment
        )
        db.session.add(review)
        db.session.commit()

        # Send notification & email to reviewee
        reviewee = db.session.get(User, reviewee_id)
        create_notification(
            user_id=reviewee_id,
            notif_type='review',
            title=f'New {rating}-Star Review Received! ⭐',
            message=f'{current_user.full_name} left you a {rating}★ review for completing "{project.title}": "{comment[:80]}..."',
            link=url_for('auth.public_profile', username=reviewee.username if reviewee else '')
        )

        msg = 'Your review has been published! Thank you for endorsing your repairman.'
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': msg, 'review': review.to_dict()})
        flash(msg, 'success')
    except Exception as e:
        db.session.rollback()
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'Could not save review.'}), 500
        flash('Could not save review. Please try again.', 'danger')

    return redirect(url_for('projects.details', id=project.id))
