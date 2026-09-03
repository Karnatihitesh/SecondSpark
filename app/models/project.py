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
    
    # Status lifecycle: Open, Help Needed, In Discussion, In Progress, Awaiting Customer Approval, Revision Required, Completed, Closed
    status = db.Column(db.String(30), default='Open', nullable=False, index=True)
    is_featured = db.Column(db.Boolean, default=False, index=True)
    views_count = db.Column(db.Integer, default=0)
    
    # Repairman Assignment & Verified Progress (0 to 100%)
    assigned_repairman_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    current_progress = db.Column(db.Integer, default=0, nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    owner = db.relationship('User', foreign_keys=[user_id], back_populates='projects')
    assigned_repairman = db.relationship('User', foreign_keys=[assigned_repairman_id], back_populates='assigned_projects')
    category = db.relationship('Category', back_populates='projects')
    images = db.relationship('ProjectImage', back_populates='project', lazy='dynamic', cascade='all, delete-orphan')
    documents = db.relationship('ProjectDocument', back_populates='project', lazy='dynamic', cascade='all, delete-orphan')
    saved_by = db.relationship('SavedProject', back_populates='project', lazy='dynamic', cascade='all, delete-orphan')
    reviews = db.relationship('Review', back_populates='project', lazy='dynamic', cascade='all, delete-orphan')
    reports = db.relationship('Report', back_populates='project', lazy='dynamic', cascade='all, delete-orphan')
    conversations = db.relationship('Conversation', back_populates='project', lazy='dynamic')
    repair_requests = db.relationship('RepairRequest', back_populates='project', lazy='dynamic', cascade='all, delete-orphan', order_by='RepairRequest.created_at.desc()')
    milestones = db.relationship('ProjectMilestone', back_populates='project', lazy='dynamic', cascade='all, delete-orphan', order_by='ProjectMilestone.order.asc()')
    progress_updates = db.relationship('ProgressUpdate', back_populates='project', lazy='dynamic', cascade='all, delete-orphan', order_by='ProgressUpdate.created_at.desc()')

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

    @property
    def latest_progress_update(self):
        return self.progress_updates.first()

    @property
    def pending_progress_update(self):
        return self.progress_updates.filter_by(status='Pending').first()

    @property
    def pending_progress(self):
        pending = self.pending_progress_update
        return pending.submitted_progress if pending else None

    @property
    def active_milestone(self):
        for m in self.milestones:
            if m.status != 'Completed':
                return m
        return self.milestones.first()

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
            'current_progress': self.current_progress,
            'pending_progress': self.pending_progress,
            'assigned_repairman': {
                'id': self.assigned_repairman.id,
                'username': self.assigned_repairman.username,
                'full_name': self.assigned_repairman.full_name,
                'avatar_url': self.assigned_repairman.avatar_url
            } if self.assigned_repairman else None,
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

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'project_id': self.project_id,
            'project': self.project.to_dict() if self.project else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class RepairRequest(db.Model):
    __tablename__ = 'repair_requests'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    repairman_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    message = db.Column(db.Text, nullable=True)
    
    # 'Pending', 'Accepted', 'Rejected', 'Cancelled'
    status = db.Column(db.String(30), default='Pending', nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    responded_at = db.Column(db.DateTime, nullable=True)

    project = db.relationship('Project', back_populates='repair_requests')
    customer = db.relationship('User', foreign_keys=[customer_id])
    repairman = db.relationship('User', foreign_keys=[repairman_id], back_populates='repair_requests_received')

    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'project_title': self.project.title if self.project else '',
            'customer': {
                'id': self.customer.id,
                'full_name': self.customer.full_name,
                'avatar_url': self.customer.avatar_url
            } if self.customer else None,
            'repairman': {
                'id': self.repairman.id,
                'full_name': self.repairman.full_name,
                'avatar_url': self.repairman.avatar_url
            } if self.repairman else None,
            'message': self.message,
            'status': self.status,
            'created_at': self.created_at.strftime('%b %d, %Y %I:%M %p') if self.created_at else '',
            'responded_at': self.responded_at.strftime('%b %d, %Y %I:%M %p') if self.responded_at else ''
        }


class ProjectMilestone(db.Model):
    __tablename__ = 'project_milestones'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    target_percentage = db.Column(db.Integer, nullable=False)
    order = db.Column(db.Integer, default=1, nullable=False)
    
    # 'Pending', 'In Progress', 'Completed'
    status = db.Column(db.String(30), default='Pending', nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    project = db.relationship('Project', back_populates='milestones')
    progress_updates = db.relationship('ProgressUpdate', back_populates='milestone', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'title': self.title,
            'description': self.description,
            'target_percentage': self.target_percentage,
            'order': self.order,
            'status': self.status,
            'completed_at': self.completed_at.strftime('%b %d, %Y') if self.completed_at else None
        }


class ProgressUpdate(db.Model):
    __tablename__ = 'progress_updates'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True)
    repairman_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    milestone_id = db.Column(db.Integer, db.ForeignKey('project_milestones.id', ondelete='SET NULL'), nullable=True, index=True)
    
    previous_progress = db.Column(db.Integer, nullable=False, default=0)
    submitted_progress = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(180), nullable=False)
    description = db.Column(db.Text, nullable=False)
    technologies_used = db.Column(db.String(255), nullable=True)
    next_step = db.Column(db.String(255), nullable=True)
    evidence_url = db.Column(db.String(255), nullable=True)
    
    # 'Pending', 'Approved', 'Revision Required'
    status = db.Column(db.String(30), default='Pending', nullable=False, index=True)
    customer_comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)

    project = db.relationship('Project', back_populates='progress_updates')
    repairman = db.relationship('User', foreign_keys=[repairman_id])
    milestone = db.relationship('ProjectMilestone', back_populates='progress_updates')

    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'repairman': {
                'id': self.repairman.id,
                'full_name': self.repairman.full_name,
                'avatar_url': self.repairman.avatar_url
            } if self.repairman else None,
            'milestone_id': self.milestone_id,
            'milestone_title': self.milestone.title if self.milestone else None,
            'previous_progress': self.previous_progress,
            'submitted_progress': self.submitted_progress,
            'title': self.title,
            'description': self.description,
            'technologies_used': self.technologies_used,
            'next_step': self.next_step,
            'evidence_url': self.evidence_url,
            'status': self.status,
            'customer_comment': self.customer_comment,
            'created_at': self.created_at.strftime('%b %d, %Y %I:%M %p') if self.created_at else '',
            'reviewed_at': self.reviewed_at.strftime('%b %d, %Y %I:%M %p') if self.reviewed_at else ''
        }

