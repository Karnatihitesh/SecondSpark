from datetime import datetime
from app.models.user import db


class Conversation(db.Model):
    __tablename__ = 'conversations'

    id = db.Column(db.Integer, primary_key=True)
    user1_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    user2_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='SET NULL'), nullable=True, index=True)
    
    last_message = db.Column(db.String(255), nullable=True)
    last_message_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user1 = db.relationship('User', foreign_keys=[user1_id])
    user2 = db.relationship('User', foreign_keys=[user2_id])
    project = db.relationship('Project', back_populates='conversations')
    messages = db.relationship('Message', back_populates='conversation', lazy='dynamic', cascade='all, delete-orphan')

    def get_other_user(self, current_user_id):
        return self.user2 if self.user1_id == current_user_id else self.user1

    def unread_count_for(self, user_id):
        return self.messages.filter_by(receiver_id=user_id, is_read=False).count()

    def __repr__(self):
        return f'<Conversation {self.id} between {self.user1_id} and {self.user2_id}>'


class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False, index=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # Relationships
    conversation = db.relationship('Conversation', back_populates='messages')
    sender = db.relationship('User', foreign_keys=[sender_id], back_populates='sent_messages')
    receiver = db.relationship('User', foreign_keys=[receiver_id], back_populates='received_messages')

    def to_dict(self):
        return {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'sender_id': self.sender_id,
            'sender_name': self.sender.full_name if self.sender else '',
            'sender_avatar': self.sender.avatar_url if self.sender else '',
            'receiver_id': self.receiver_id,
            'content': self.content,
            'is_read': self.is_read,
            'created_at': self.created_at.strftime('%I:%M %p') if self.created_at else '',
            'created_date': self.created_at.strftime('%b %d, %Y') if self.created_at else ''
        }

    def __repr__(self):
        return f'<Message {self.id} from {self.sender_id}>'
