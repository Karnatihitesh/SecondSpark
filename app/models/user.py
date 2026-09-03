from datetime import datetime, timedelta
import secrets, string
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class UserRole:
    CUSTOMER = 'customer'
    TECHNICIAN = 'technician'
    ADMIN = 'admin'

    CHOICES = [CUSTOMER, TECHNICIAN, ADMIN]


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    bio = db.Column(db.Text, nullable=True)
    skills = db.Column(db.String(255), nullable=True)  # Comma-separated or JSON string
    technologies = db.Column(db.String(255), nullable=True)  # Comma-separated frameworks & tools
    specialization = db.Column(db.String(100), nullable=True)  # Primary domain
    experience = db.Column(db.Text, nullable=True)  # Years of experience / background
    availability = db.Column(db.String(30), default='Available')  # 'Available', 'Busy', 'Not Available'
    location = db.Column(db.String(100), nullable=True)
    avatar_url = db.Column(db.String(255), nullable=True, default='/static/images/default-avatar.svg')
    role = db.Column(db.String(20), nullable=False, default=UserRole.CUSTOMER)  # 'customer', 'technician', 'admin'
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    projects = db.relationship('Project', foreign_keys='Project.user_id', back_populates='owner', lazy='dynamic', cascade='all, delete-orphan')
    assigned_projects = db.relationship('Project', foreign_keys='Project.assigned_repairman_id', back_populates='assigned_repairman', lazy='dynamic')
    repair_requests_received = db.relationship('RepairRequest', foreign_keys='RepairRequest.repairman_id', back_populates='repairman', lazy='dynamic')
    saved_projects = db.relationship('SavedProject', back_populates='user', lazy='dynamic', cascade='all, delete-orphan')
    sent_messages = db.relationship('Message', foreign_keys='Message.sender_id', back_populates='sender', lazy='dynamic')
    received_messages = db.relationship('Message', foreign_keys='Message.receiver_id', back_populates='receiver', lazy='dynamic')
    notifications = db.relationship('Notification', back_populates='user', lazy='dynamic', cascade='all, delete-orphan')
    reviews_given = db.relationship('Review', foreign_keys='Review.reviewer_id', back_populates='reviewer', lazy='dynamic')
    reviews_received = db.relationship('Review', foreign_keys='Review.reviewee_id', back_populates='reviewee', lazy='dynamic')
    reports_filed = db.relationship('Report', foreign_keys='Report.reporter_id', back_populates='reporter', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == UserRole.ADMIN

    @property
    def is_customer(self):
        return self.role in [UserRole.CUSTOMER, 'user']

    @property
    def is_technician(self):
        return self.role == UserRole.TECHNICIAN

    @property
    def display_role(self):
        if self.is_admin:
            return 'Administrator'
        elif self.is_technician:
            return 'Verified Technician'
        return 'Customer'

    @property
    def skills_list(self):
        if not self.skills:
            return []
        return [s.strip() for s in self.skills.split(',') if s.strip()]

    @property
    def technologies_list(self):
        if not self.technologies:
            return []
        return [t.strip() for t in self.technologies.split(',') if t.strip()]

    @property
    def rating_summary(self):
        reviews = self.reviews_received.all()
        if not reviews:
            return {'average': 0.0, 'count': 0}
        avg = sum(r.rating for r in reviews) / len(reviews)
        return {'average': round(avg, 1), 'count': len(reviews)}

    @property
    def average_rating(self):
        return self.rating_summary['average']

    @property
    def reviews_count(self):
        return self.reviews_received.count()

    @property
    def projects_uploaded_count(self):
        return self.projects.count()

    @property
    def projects_repaired_count(self):
        from app.models.project import Project
        return self.assigned_projects.filter(Project.status == 'Completed').count()

    @property
    def active_repairs_count(self):
        from app.models.project import Project
        return self.assigned_projects.filter(Project.status.in_(['Assigned', 'In Progress', 'Awaiting Customer Approval', 'Revision Required'])).count()

    @property
    def success_rate(self):
        from app.models.project import Project
        completed = self.projects_repaired_count
        closed = self.assigned_projects.filter(Project.status == 'Closed').count()
        total = completed + closed
        if total == 0:
            return 100
        return int(round((completed / total) * 100))

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'bio': self.bio,
            'skills': self.skills_list,
            'technologies': self.technologies_list,
            'specialization': self.specialization,
            'experience': self.experience,
            'availability': self.availability,
            'location': self.location,
            'avatar_url': self.avatar_url,
            'role': self.role,
            'display_role': self.display_role,
            'rating': self.average_rating,
            'reviews_count': self.reviews_count,
            'projects_repaired_count': self.projects_repaired_count,
            'projects_uploaded_count': self.projects_uploaded_count,
            'success_rate': self.success_rate,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<User {self.username}>'


class VerificationCode(db.Model):
    """Short-lived, securely hashed OTP for password reset / email verification."""
    __tablename__ = 'verification_codes'

    id          = db.Column(db.Integer, primary_key=True)
    email       = db.Column(db.String(120), nullable=False, index=True)
    code        = db.Column(db.String(255), nullable=False)  # Securely hashed OTP
    purpose     = db.Column(db.String(30), default='password_reset')
    is_used     = db.Column(db.Boolean, default=False)
    expires_at  = db.Column(db.DateTime, nullable=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    @classmethod
    def generate(cls, email: str, purpose: str = 'password_reset', ttl_minutes: int = 10):
        """Create and return a new OTP instance and the raw 6-digit plain code for email dispatch."""
        raw_code = ''.join(secrets.choice(string.digits) for _ in range(6))
        hashed_code = generate_password_hash(raw_code)
        otp = cls(
            email=email.lower().strip(),
            code=hashed_code,
            purpose=purpose,
            expires_at=datetime.utcnow() + timedelta(minutes=ttl_minutes)
        )
        db.session.add(otp)
        db.session.commit()
        return otp, raw_code

    @classmethod
    def verify(cls, email: str, code: str, purpose: str = 'password_reset'):
        """Verify the submitted OTP against the stored hash and return record if valid."""
        records = cls.query.filter_by(
            email=email.lower().strip(),
            purpose=purpose,
            is_used=False
        ).order_by(cls.created_at.desc()).all()

        now = datetime.utcnow()
        for rec in records:
            if rec.expires_at > now:
                if rec.code.startswith('scrypt:') or rec.code.startswith('pbkdf2:'):
                    if check_password_hash(rec.code, code):
                        return rec
                elif rec.code == code:
                    return rec
        return None

    def mark_used(self):
        self.is_used = True
        db.session.commit()

    def __repr__(self):
        return f'<OTP {self.email} [{self.purpose}]>'

