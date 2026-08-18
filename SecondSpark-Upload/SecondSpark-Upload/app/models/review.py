from datetime import datetime
from app.models.user import db


class Review(db.Model):
    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    reviewee_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    rating = db.Column(db.Integer, nullable=False)  # 1 to 5
    comment = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # Unique constraint: only 1 review per project from same reviewer to same reviewee
    __table_args__ = (db.UniqueConstraint('project_id', 'reviewer_id', 'reviewee_id', name='uq_project_review'),)

    # Relationships
    project = db.relationship('Project', back_populates='reviews')
    reviewer = db.relationship('User', foreign_keys=[reviewer_id], back_populates='reviews_given')
    reviewee = db.relationship('User', foreign_keys=[reviewee_id], back_populates='reviews_received')

    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'project_title': self.project.title if self.project else '',
            'reviewer': {
                'id': self.reviewer.id,
                'username': self.reviewer.username,
                'full_name': self.reviewer.full_name,
                'avatar_url': self.reviewer.avatar_url
            } if self.reviewer else None,
            'rating': self.rating,
            'comment': self.comment,
            'created_at': self.created_at.strftime('%b %d, %Y') if self.created_at else ''
        }

    def __repr__(self):
        return f'<Review {self.rating}* by User {self.reviewer_id} on Project {self.project_id}>'
