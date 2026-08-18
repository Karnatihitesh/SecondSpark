from datetime import datetime
from app.models.user import db


class Project(db.Model):
    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id', ondelete='SET NULL'), nullable=True, index=True)
    
    title = db.Column(db.String(200), nullable=False, index=True)
    slug = db.Column(db.String(220), unique=True, nullable=False, index=True)
    short_summary = db.Column(db.String(350), nullable=False)
    description = db.Column(db.Text, nullable=False)
    
    current_condition = db.Column(db.String(50), nullable=False, default='Incomplete')  # 'Abandoned', 'Incomplete', 'Faulty', 'Hardware Issues', 'Untested'
    problems_faults = db.Column(db.Text, nullable=False)
    help_required = db.Column(db.Text, nullable=False)
    required_skills = db.Column(db.String(300), nullable=False)  # Comma separated
    
    budget = db.Column(db.Float, default=0.0)
    budget_type = db.Column(db.String(20), default='Fixed')  # 'Fixed', 'Hourly', 'Collaboration/Open'
    location = db.Column(db.String(150), default='Remote')
    deadline = db.Column(db.String(100), nullable=True)
    
    # Status lifecycle: Open, Help Needed, In Discussion, In Progress, Completed, Closed
    status = db.Column(db.String(30), default='Open', nullable=False, index=True)
    is_featured = db.Column(db.Boolean, default=False, index=True)
    views_count = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    owner = db.relationship('User', back_populates='projects')
    category = db.relationship('Category', back_populates='projects')
    images = db.relationship('ProjectImage', back_populates='project', lazy='dynamic', cascade='all, delete-orphan')
    documents = db.relationship('ProjectDocument', back_populates='project', lazy='dynamic', cascade='all, delete-orphan')
    saved_by = db.relationship('SavedProject', back_populates='project', lazy='dynamic', cascade='all, delete-orphan')
    reviews = db.relationship('Review', back_populates='project', lazy='dynamic', cascade='all, delete-orphan')
    reports = db.relationship('Report', back_populates='project', lazy='dynamic', cascade='all, delete-orphan')
    conversations = db.relationship('Conversation', back_populates='project', lazy='dynamic')

    @property
    def skills_list(self):
        if not self.required_skills:
            return []
        return [s.strip() for s in self.required_skills.split(',') if s.strip()]

    @property
    def primary_image(self):
        img = self.images.filter_by(is_primary=True).first()
        if not img:
            img = self.images.first()
        return img.image_url if img else '/static/images/project-placeholder.svg'

    @property
    def saves_count(self):
        return self.saved_by.count()

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'slug': self.slug,
            'short_summary': self.short_summary,
            'description': self.description,
            'category': self.category.name if self.category else 'General',
            'category_slug': self.category.slug if self.category else 'general',
            'current_condition': self.current_condition,
            'problems_faults': self.problems_faults,
            'help_required': self.help_required,
            'required_skills': self.skills_list,
            'budget': self.budget,
            'location': self.location,
            'status': self.status,
            'primary_image': self.primary_image,
            'owner': {
                'id': self.owner.id,
                'username': self.owner.username,
                'full_name': self.owner.full_name,
                'avatar_url': self.owner.avatar_url
            } if self.owner else None,
            'created_at': self.created_at.strftime('%b %d, %Y') if self.created_at else ''
        }

    def __repr__(self):
        return f'<Project {self.title}>'


class ProjectImage(db.Model):
    __tablename__ = 'project_images'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True)
    image_url = db.Column(db.String(255), nullable=False)
    caption = db.Column(db.String(150), nullable=True)
    is_primary = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    project = db.relationship('Project', back_populates='images')


class ProjectDocument(db.Model):
    __tablename__ = 'project_documents'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True)
    file_url = db.Column(db.String(255), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_size_kb = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    project = db.relationship('Project', back_populates='documents')


class SavedProject(db.Model):
    __tablename__ = 'saved_projects'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Unique constraint so a user can't save same project twice
    __table_args__ = (db.UniqueConstraint('user_id', 'project_id', name='uq_user_saved_project'),)

    user = db.relationship('User', back_populates='saved_projects')
    project = db.relationship('Project', back_populates='saved_by')
