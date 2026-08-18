from flask import Blueprint, request, redirect, url_for, flash
from app.models.user import db
from app.models.report import Report
from app.services.auth_service import get_current_user, login_required

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')


@reports_bp.route('/create', methods=['POST'])
@login_required
def create():
    current_user = get_current_user()
    project_id = request.form.get('project_id', type=int)
    reported_user_id = request.form.get('reported_user_id', type=int)
    reason = request.form.get('reason', '').strip()
    description = request.form.get('description', '').strip()

    if not reason or not description:
        flash('Please select a reason and describe the issue for reporting.', 'danger')
        return redirect(request.referrer or url_for('projects.browse'))

    try:
        report = Report(
            reporter_id=current_user.id,
            reported_user_id=reported_user_id,
            project_id=project_id,
            reason=reason,
            description=description,
            status='Pending'
        )
        db.session.add(report)
        db.session.commit()
        flash('Thank you. Your report has been submitted to the moderation team for review.', 'info')
    except Exception as e:
        db.session.rollback()
        flash('Failed to submit report. Please try again.', 'danger')

    return redirect(request.referrer or url_for('projects.browse'))
