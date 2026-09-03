from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
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

    # Determine reviewee: if current_user is owner, reviewee is collaborator; if current_user is collaborator, reviewee is owner
    reviewee_id = request.form.get('reviewee_id', type=int)
    if not reviewee_id:
        if current_user.id != project.user_id:
            reviewee_id = project.user_id
        else:
            # If owner is reviewing, default to first collaborator or passed reviewee
            first_convo = project.conversations.first()
            if first_convo:
                reviewee_id = first_convo.get_other_user(current_user.id).id
            else:
                flash('No collaborator found on this project to review yet.', 'warning')
                return redirect(url_for('projects.details', id=project.id))

    if reviewee_id == current_user.id:
        flash('You cannot review yourself.', 'warning')
        return redirect(url_for('projects.details', id=project.id))

    rating = request.form.get('rating', type=int)
    comment = request.form.get('comment', '').strip()

    if not rating or rating < 1 or rating > 5 or not comment:
        flash('Please provide a star rating (1-5) and written feedback.', 'danger')
        return redirect(url_for('projects.details', id=project.id))

    # Check for duplicate review
    existing = Review.query.filter_by(
        project_id=project.id,
        reviewer_id=current_user.id,
        reviewee_id=reviewee_id
    ).first()

    if existing:
        flash('You have already submitted a review for this project collaboration.', 'warning')
        return redirect(url_for('projects.details', id=project.id))

    try:
        review = Review(
            project_id=project.id,
            reviewer_id=current_user.id,
            reviewee_id=reviewee_id,
            rating=rating,
            comment=comment
        )
        db.session.add(review)
        db.session.commit()

        # Send notification & email to reviewee
        reviewee = db.session.get(User, reviewee_id)
        create_notification(
            user_id=reviewee_id,
            notif_type='review',
            title=f'New {rating}-Star Review Received!',
            message=f'{current_user.full_name} left you a {rating}★ review on project "{project.title}": "{comment[:80]}..."',
            link=url_for('auth.public_profile', username=reviewee.username if reviewee else '')
        )

        flash('Your review has been published! Thank you for supporting the SecondSpark community.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Could not save review. Please try again.', 'danger')

    return redirect(url_for('projects.details', id=project.id))
