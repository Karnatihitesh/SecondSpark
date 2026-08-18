from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.models.user import db
from app.models.notification import Notification
from app.services.auth_service import get_current_user, login_required

notifications_bp = Blueprint('notifications', __name__, url_prefix='/notifications')


@notifications_bp.route('/')
@login_required
def index():
    user = get_current_user()
    notifications = user.notifications.order_by(Notification.created_at.desc()).all()
    return render_template('notifications.html', notifications=notifications)


@notifications_bp.route('/<int:id>/read', methods=['POST'])
@login_required
def mark_read(id):
    user = get_current_user()
    notif = Notification.query.filter_by(id=id, user_id=user.id).first_or_404()
    notif.is_read = True
    db.session.commit()

    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True})
    
    if notif.link:
        return redirect(notif.link)
    return redirect(url_for('notifications.index'))


@notifications_bp.route('/mark-all-read', methods=['POST'])
@login_required
def mark_all_read():
    user = get_current_user()
    Notification.query.filter_by(user_id=user.id, is_read=False).update({'is_read': True})
    db.session.commit()

    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True})

    flash('All notifications marked as read.', 'success')
    return redirect(url_for('notifications.index'))
