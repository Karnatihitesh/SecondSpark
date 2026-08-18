from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from app.models.user import db, User
from app.models.message import Conversation, Message
from app.models.project import Project
from app.services.auth_service import get_current_user, login_required
from app.services.notification_service import create_notification

messages_bp = Blueprint('messages', __name__, url_prefix='/messages')


@messages_bp.route('/')
@messages_bp.route('/<int:conversation_id>')
@login_required
def index(conversation_id=None):
    user = get_current_user()

    conversations = Conversation.query.filter(
        (Conversation.user1_id == user.id) | (Conversation.user2_id == user.id)
    ).order_by(Conversation.last_message_at.desc()).all()

    active_conversation = None
    messages = []
    other_user = None

    if conversation_id:
        active_conversation = db.session.get(Conversation, conversation_id)
        if not active_conversation:
            abort(404)
        if active_conversation.user1_id != user.id and active_conversation.user2_id != user.id:
            abort(403)
        
        unread_msgs = Message.query.filter_by(
            conversation_id=active_conversation.id,
            receiver_id=user.id,
            is_read=False
        ).all()
        if unread_msgs:
            for m in unread_msgs:
                m.is_read = True
            db.session.commit()

        messages = active_conversation.messages.order_by(Message.created_at.asc()).all()
        other_user = active_conversation.get_other_user(user.id)
    elif conversations:
        active_conversation = conversations[0]
        unread_msgs = Message.query.filter_by(
            conversation_id=active_conversation.id,
            receiver_id=user.id,
            is_read=False
        ).all()
        if unread_msgs:
            for m in unread_msgs:
                m.is_read = True
            db.session.commit()

        messages = active_conversation.messages.order_by(Message.created_at.asc()).all()
        other_user = active_conversation.get_other_user(user.id)

    return render_template(
        'messages.html',
        conversations=conversations,
        active_conversation=active_conversation,
        messages=messages,
        other_user=other_user
    )


@messages_bp.route('/start/user/<int:user_id>', methods=['GET', 'POST'])
@messages_bp.route('/start/project/<int:project_id>', methods=['GET', 'POST'])
@login_required
def start_conversation(user_id=None, project_id=None):
    current_user = get_current_user()
    project = None

    if project_id:
        project = db.session.get(Project, project_id)
        if not project:
            abort(404)
        target_user = project.owner
    elif user_id:
        target_user = db.session.get(User, user_id)
        if not target_user:
            abort(404)
    else:
        abort(400)

    if target_user.id == current_user.id:
        flash('You cannot message yourself.', 'warning')
        return redirect(request.referrer or url_for('projects.browse'))

    conv = Conversation.query.filter(
        ((Conversation.user1_id == current_user.id) & (Conversation.user2_id == target_user.id)) |
        ((Conversation.user1_id == target_user.id) & (Conversation.user2_id == current_user.id))
    ).first()

    if not conv:
        conv = Conversation(
            user1_id=current_user.id,
            user2_id=target_user.id,
            project_id=project.id if project else None,
            last_message="Conversation started",
            last_message_at=datetime.utcnow()
        )
        db.session.add(conv)
        db.session.commit()

    offer_msg = request.form.get('initial_message') or request.args.get('initial_message')
    if offer_msg and offer_msg.strip():
        msg = Message(
            conversation_id=conv.id,
            sender_id=current_user.id,
            receiver_id=target_user.id,
            content=offer_msg.strip(),
            is_read=False
        )
        conv.last_message = offer_msg.strip()[:100]
        conv.last_message_at = datetime.utcnow()
        db.session.add(msg)
        db.session.commit()

        proj_title = f' on "{project.title}"' if project else ''
        create_notification(
            user_id=target_user.id,
            notif_type='message',
            title='New Collaboration Message',
            message=f'{current_user.full_name} sent you a message{proj_title}: "{offer_msg[:60]}..."',
            link=url_for('messages.index', conversation_id=conv.id)
        )

    return redirect(url_for('messages.index', conversation_id=conv.id))


@messages_bp.route('/<int:conversation_id>/send', methods=['POST'])
@login_required
def send(conversation_id):
    current_user = get_current_user()
    conv = db.session.get(Conversation, conversation_id)
    if not conv:
        abort(404)

    if conv.user1_id != current_user.id and conv.user2_id != current_user.id:
        abort(403)

    content = request.form.get('content', '').strip()
    if not content:
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'Message cannot be empty'}), 400
        return redirect(url_for('messages.index', conversation_id=conv.id))

    receiver = conv.get_other_user(current_user.id)

    msg = Message(
        conversation_id=conv.id,
        sender_id=current_user.id,
        receiver_id=receiver.id,
        content=content,
        is_read=False
    )
    conv.last_message = content[:100]
    conv.last_message_at = datetime.utcnow()

    db.session.add(msg)
    db.session.commit()

    create_notification(
        user_id=receiver.id,
        notif_type='message',
        title=f'New Message from {current_user.full_name}',
        message=f'"{content[:80]}..."',
        link=url_for('messages.index', conversation_id=conv.id)
    )

    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'message': msg.to_dict()
        })

    return redirect(url_for('messages.index', conversation_id=conv.id))
