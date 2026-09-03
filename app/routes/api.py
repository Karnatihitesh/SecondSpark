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
    """Toggle save/bookmark status of a project for the authenticated user."""
    user = get_current_user()
    project = db.session.get(Project, id)
    if not project:
        return jsonify({'success': False, 'error': 'Project not found'}), 404

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

    return jsonify({
        'success': True,
        'saved': saved,
        'message': msg,
        'saves_count': project.saves_count
    })


@api_bp.route('/projects/<int:id>/save-action', methods=['POST'])
@login_required
def save_project_explicit(id):
    """Explicitly save a project (idempotent, prevents duplicate saves)."""
    user = get_current_user()
    project = db.session.get(Project, id)
    if not project:
        return jsonify({'success': False, 'error': 'Project not found'}), 404

    existing = SavedProject.query.filter_by(user_id=user.id, project_id=project.id).first()
    if not existing:
        sp = SavedProject(user_id=user.id, project_id=project.id)
        db.session.add(sp)
        db.session.commit()

    return jsonify({
        'success': True,
        'saved': True,
        'message': 'Project saved to bookmarks!',
        'saves_count': project.saves_count
    })


@api_bp.route('/projects/<int:id>/unsave', methods=['POST', 'DELETE'])
@api_bp.route('/projects/<int:id>/save', methods=['DELETE'])
@login_required
def unsave_project_explicit(id):
    """Explicitly unsave/remove a project (idempotent)."""
    user = get_current_user()
    project = db.session.get(Project, id)
    if not project:
        return jsonify({'success': False, 'error': 'Project not found'}), 404

    existing = SavedProject.query.filter_by(user_id=user.id, project_id=project.id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()

    return jsonify({
        'success': True,
        'saved': False,
        'message': 'Project removed from bookmarks.',
        'saves_count': project.saves_count
    })


@api_bp.route('/projects/<int:id>/is-saved', methods=['GET'])
@api_bp.route('/projects/<int:id>/save', methods=['GET'])
def check_is_saved(id):
    """Check whether a project is currently saved by the authenticated user."""
    project = db.session.get(Project, id)
    if not project:
        return jsonify({'success': False, 'error': 'Project not found'}), 404

    user = get_current_user()
    is_saved = False
    if user:
        is_saved = SavedProject.query.filter_by(user_id=user.id, project_id=project.id).first() is not None

    return jsonify({
        'success': True,
        'is_saved': is_saved,
        'saves_count': project.saves_count
    })


@api_bp.route('/user/saved-projects', methods=['GET'])
@login_required
def get_user_saved_projects():
    """Retrieve all saved projects for the currently authenticated user."""
    user = get_current_user()
    saved_items = user.saved_projects.order_by(SavedProject.created_at.desc()).all()
    results = []
    for sp in saved_items:
        if sp.project:
            p = sp.project
            results.append({
                'id': p.id,
                'title': p.title,
                'slug': p.slug,
                'category': p.category.name if p.category else 'General',
                'status': p.status,
                'budget': p.budget,
                'image': p.primary_image,
                'url': f"/projects/{p.id}",
                'saved_at': sp.created_at.isoformat() if sp.created_at else None
            })

    return jsonify({
        'success': True,
        'count': len(results),
        'saved_projects': results
    })

