from datetime import datetime
from app.models.user import db


class Report(db.Model):
    __tablename__ = 'reports'

    id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    reported_user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=True, index=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=True, index=True)
    
    reason = db.Column(db.String(100), nullable=False)  # 'Spam', 'Inappropriate Content', 'Copyright Violation', 'Scam/Fraud', 'Harassment', 'Other'
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(30), default='Pending')  # 'Pending', 'Reviewed', 'Dismissed', 'Resolved'
    admin_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    resolved_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    reporter = db.relationship('User', foreign_keys=[reporter_id], back_populates='reports_filed')
    reported_user = db.relationship('User', foreign_keys=[reported_user_id])
    project = db.relationship('Project', back_populates='reports')

    def to_dict(self):
        return {
            'id': self.id,
            'reason': self.reason,
            'description': self.description,
            'status': self.status,
            'project_title': self.project.title if self.project else None,
            'project_id': self.project_id,
            'reporter_name': self.reporter.full_name if self.reporter else 'Anonymous',
            'reported_user_name': self.reported_user.full_name if self.reported_user else None,
            'created_at': self.created_at.strftime('%b %d, %Y') if self.created_at else ''
        }

    def __repr__(self):
        return f'<Report {self.id}: {self.reason}>'
