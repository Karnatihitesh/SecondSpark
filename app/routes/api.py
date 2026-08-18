from flask import Blueprint, request, jsonify
from app.models.user import db, User
from app.models.project import Project, SavedProject
from app.models.message import Conversation, Message
from app.models.notification import Notification
from app.services.auth_service import get_current_user, login_required
from app.services.project_service import build_project_query

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/search')
def live_search():
    query_str = request.args.get('q', '').strip()
    if not query_str:
        return jsonify({'results': []})

    projects = build_project_query(search=query_str).limit(6).all()
    results = []
    for p in projects:
        results.append({
            'id': p.id,
            'title': p.title,
            'category': p.category.name if p.category else 'General',
            'status': p.status,
            'budget': p.budget,
            'image': p.primary_image,
            'url': f"/projects/{p.id}"
        })

    return jsonify({'results': results})


@api_bp.route('/messages/poll')
@login_required
def poll_messages():
    user = get_current_user()
    conversation_id = request.args.get('conversation_id', type=int)
    last_id = request.args.get('last_id', 0, type=int)

    if not conversation_id:
        return jsonify({'messages': []})

    conv = Conversation.query.get_or_404(conversation_id)
    if conv.user1_id != user.id and conv.user2_id != user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    # Query new messages after last_id
    new_messages = conv.messages.filter(Message.id > last_id).order_by(Message.created_at.asc()).all()
    
    # Mark incoming as read
    for m in new_messages:
        if m.receiver_id == user.id:
            m.is_read = True
    if new_messages:
        db.session.commit()

    return jsonify({
        'messages': [m.to_dict() for m in new_messages]
    })


@api_bp.route('/user/counts')
@login_required
def user_counts():
    user = get_current_user()
    unread_messages = Message.query.filter_by(receiver_id=user.id, is_read=False).count()
    unread_notifications = Notification.query.filter_by(user_id=user.id, is_read=False).count()
    return jsonify({
        'unread_messages': unread_messages,
        'unread_notifications': unread_notifications
    })


@api_bp.route('/projects/<int:id>/save', methods=['POST'])
@login_required
def toggle_save(id):
    user = get_current_user()
    project = Project.query.get_or_404(id)

    existing = SavedProject.query.filter_by(user_id=user.id, project_id=project.id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        saved = False
        msg = 'Removed from saved projects.'
    else:
        sp = SavedProject(user_id=user.id, project_id=project.id)
        db.session.add(sp)
        db.session.commit()
        saved = True
        msg = 'Project saved!'

    return jsonify({
        'success': True,
        'saved': saved,
        'message': msg,
        'saves_count': project.saves_count
    })
