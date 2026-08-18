from datetime import datetime
from app.models.user import db


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    slug = db.Column(db.String(80), unique=True, nullable=False, index=True)
    icon = db.Column(db.String(50), nullable=True, default='fa-folder')
    description = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    projects = db.relationship('Project', back_populates='category', lazy='dynamic')

    @property
    def project_count(self):
        return self.projects.filter_by(status='Open').count()

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'icon': self.icon,
            'description': self.description,
            'project_count': self.project_count
        }

    def __repr__(self):
        return f'<Category {self.name}>'
