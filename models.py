"""
SQLAlchemy database models for HR system.
Supports PostgreSQL for production use.
"""

from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Index, CheckConstraint
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    """HR system users with role-based access."""
    __tablename__ = 'users'

    id = db.Column(db.String(36), primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default='hr', nullable=False)  # 'admin', 'hr', 'interviewer'
    department = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)
    last_login_ip = db.Column(db.String(45), nullable=True)  # IPv4 or IPv6

    # Relationships
    activity_logs = db.relationship('ActivityLog', backref='user', lazy='dynamic', foreign_keys='ActivityLog.user_id')
    interviews_scheduled = db.relationship('Interview', backref='interviewer', lazy='dynamic', foreign_keys='Interview.interviewer_id')

    def set_password(self, password):
        """Hash and set password."""
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        """Verify password against hash."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.email}>'


class JobPosting(db.Model):
    """Job positions open for recruitment."""
    __tablename__ = 'job_postings'

    id = db.Column(db.String(36), primary_key=True)
    title = db.Column(db.String(255), nullable=False, index=True)
    department = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    requirements = db.Column(db.JSON, nullable=True)  # List of requirements
    custom_screening_criteria = db.Column(db.Text, nullable=True)
    
    application_link = db.Column(db.String(500), nullable=True)
    salary_range = db.Column(db.String(100), nullable=True)  # e.g., "50000-70000"
    employment_type = db.Column(db.String(50), default='Full-time')  # Full-time, Part-time, Contract
    
    due_date = db.Column(db.DateTime, nullable=False, index=True)
    status = db.Column(db.String(50), default='open', nullable=False)  # open, closed, archived
    
    created_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    applications = db.relationship('Application', backref='job', lazy='dynamic', cascade='all, delete-orphan')

    __table_args__ = (
        Index('idx_job_status_due_date', 'status', 'due_date'),
    )

    def __repr__(self):
        return f'<JobPosting {self.title}>'


class Application(db.Model):
    """Job applications from candidates."""
    __tablename__ = 'applications'

    id = db.Column(db.String(36), primary_key=True)
    job_id = db.Column(db.String(36), db.ForeignKey('job_postings.id'), nullable=False, index=True)
    
    full_name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, index=True)
    phone = db.Column(db.String(20), nullable=False)
    highest_education = db.Column(db.String(100), nullable=False)
    
    resume_path = db.Column(db.String(500), nullable=False)
    certifications = db.Column(db.JSON, nullable=True)  # List of file paths
    cover_letter = db.Column(db.Text, nullable=True)
    
    screening_score = db.Column(db.Float, default=0.0, nullable=False)
    matched_skills = db.Column(db.JSON, nullable=True)
    missing_skills = db.Column(db.JSON, nullable=True)
    screening_summary = db.Column(db.Text, nullable=True)
    recommendation = db.Column(db.String(100), nullable=True)  # 'Strong hire', 'Interview', etc.
    
    status = db.Column(db.String(50), default='pending', nullable=False, index=True)  # pending, shortlisted, rejected, interview, hired, archived
    hr_notes = db.Column(db.Text, nullable=True)
    hr_rating = db.Column(db.Float, nullable=True)  # 1-5 star rating
    
    applied_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    screened_at = db.Column(db.DateTime, nullable=True)
    screened_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    interview = db.relationship('Interview', backref='application', uselist=False, cascade='all, delete-orphan')
    activity_logs = db.relationship('ActivityLog', backref='application', lazy='dynamic', cascade='all, delete-orphan')

    __table_args__ = (
        Index('idx_app_job_status', 'job_id', 'status'),
        Index('idx_app_score', 'screening_score'),
        CheckConstraint('screening_score >= 0 AND screening_score <= 100'),
    )

    def __repr__(self):
        return f'<Application {self.full_name}>'


class Interview(db.Model):
    """Interview scheduling and tracking."""
    __tablename__ = 'interviews'

    id = db.Column(db.String(36), primary_key=True)
    application_id = db.Column(db.String(36), db.ForeignKey('applications.id'), nullable=False, index=True, unique=True)
    
    interview_date = db.Column(db.DateTime, nullable=False, index=True)
    interview_type = db.Column(db.String(50), default='phone', nullable=False)  # phone, video, in-person
    interview_link = db.Column(db.String(500), nullable=True)  # Zoom/Teams link for remote
    interview_location = db.Column(db.String(500), nullable=True)  # Address for in-person
    
    interviewer_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    interview_notes = db.Column(db.Text, nullable=True)
    interviewer_rating = db.Column(db.Float, nullable=True)  # 1-5
    interviewer_feedback = db.Column(db.Text, nullable=True)
    
    status = db.Column(db.String(50), default='scheduled', nullable=False)  # scheduled, completed, cancelled, no-show
    
    reminder_sent_at = db.Column(db.DateTime, nullable=True)
    email_sent_at = db.Column(db.DateTime, nullable=True)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self):
        return f'<Interview {self.id}>'


class ActivityLog(db.Model):
    """Audit trail for all user actions and system events."""
    __tablename__ = 'activity_logs'

    id = db.Column(db.String(36), primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    application_id = db.Column(db.String(36), db.ForeignKey('applications.id'), nullable=True, index=True)
    
    action = db.Column(db.String(100), nullable=False, index=True)  # login, logout, view_application, etc.
    action_type = db.Column(db.String(50), nullable=False)  # user_action, system_action, error
    
    details = db.Column(db.Text, nullable=True)
    changes_before = db.Column(db.JSON, nullable=True)  # For tracking updates
    changes_after = db.Column(db.JSON, nullable=True)
    
    ip_address = db.Column(db.String(45), nullable=True)  # IPv4 or IPv6
    user_agent = db.Column(db.String(500), nullable=True)
    
    status = db.Column(db.String(50), default='success', nullable=False)  # success, failure, warning
    error_message = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    __table_args__ = (
        Index('idx_activity_user_date', 'user_id', 'created_at'),
        Index('idx_activity_action_date', 'action', 'created_at'),
    )

    def __repr__(self):
        return f'<ActivityLog {self.action}>'


class SystemSettings(db.Model):
    """Global system configuration settings."""
    __tablename__ = 'system_settings'

    id = db.Column(db.Integer, primary_key=True)
    
    company_name = db.Column(db.String(255), default='Global Modern Business', nullable=False)
    company_logo_url = db.Column(db.String(500), nullable=True)
    support_email = db.Column(db.String(255), nullable=False)
    support_phone = db.Column(db.String(20), nullable=True)
    
    # Email settings
    email_enabled = db.Column(db.Boolean, default=True)
    smtp_host = db.Column(db.String(255), nullable=True)
    smtp_port = db.Column(db.Integer, nullable=True)
    smtp_username = db.Column(db.String(255), nullable=True)
    smtp_password = db.Column(db.String(255), nullable=True)
    smtp_use_tls = db.Column(db.Boolean, default=True)
    
    # Notification settings
    notify_on_application = db.Column(db.Boolean, default=True)
    notify_on_interview = db.Column(db.Boolean, default=True)
    notify_on_screening = db.Column(db.Boolean, default=True)
    
    # Auto-screening settings
    auto_screen_on_due_date = db.Column(db.Boolean, default=True)
    auto_screen_enabled = db.Column(db.Boolean, default=True)
    
    # UI settings
    theme = db.Column(db.String(50), default='light')  # light, dark
    items_per_page = db.Column(db.Integer, default=25)
    
    # Session/security
    session_timeout_minutes = db.Column(db.Integer, default=480)  # 8 hours
    password_reset_token_expiry_hours = db.Column(db.Integer, default=24)
    
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self):
        return '<SystemSettings>'


class EmailTemplate(db.Model):
    """Email templates for notifications."""
    __tablename__ = 'email_templates'

    id = db.Column(db.String(36), primary_key=True)
    
    name = db.Column(db.String(100), nullable=False, unique=True)
    subject = db.Column(db.String(255), nullable=False)
    body_html = db.Column(db.Text, nullable=False)
    body_text = db.Column(db.Text, nullable=True)
    
    variables = db.Column(db.JSON, nullable=True)  # e.g., ['candidate_name', 'interview_date', 'company_name']
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self):
        return f'<EmailTemplate {self.name}>'
