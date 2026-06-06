"""
Configuration settings for HR System Flask application.
Supports different environments and email/database configurations.
"""

import os
from datetime import timedelta

class Config:
    """Base configuration."""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = False
    TESTING = False
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_DURATION = timedelta(days=30)
    
    # Database configuration
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    
    # File upload settings
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt', 'doc'}
    ALLOWED_CERT_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png'}
    
    # Email configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', True)
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'noreply@company.com'
    
    # Application settings
    COMPANY_NAME = os.environ.get('COMPANY_NAME') or 'Global Modern Business'
    SUPPORT_EMAIL = os.environ.get('SUPPORT_EMAIL') or 'support@company.com'
    SUPPORT_PHONE = os.environ.get('SUPPORT_PHONE') or '+1-800-123-4567'
    
    # HR System settings
    ITEMS_PER_PAGE = 25
    SESSION_TIMEOUT_MINUTES = 480  # 8 hours
    PASSWORD_RESET_TOKEN_EXPIRY_HOURS = 24
    
    # Security
    RATE_LIMIT_ENABLED = True
    RATE_LIMIT_STORAGE = 'memory'  # Can be 'memory' or 'redis'
    
    # Logging
    LOG_LEVEL = 'INFO'
    LOG_FILE = 'hr_system.log'
    
    # Feature flags
    ENABLE_AUTO_SCREENING = True
    ENABLE_EMAIL_NOTIFICATIONS = True
    ENABLE_INTERVIEW_REMINDERS = True
    ENABLE_WEEKLY_REPORTS = True
    ENABLE_BACKGROUND_JOBS = True


class DevelopmentConfig(Config):
    """Development environment configuration."""
    
    DEBUG = True
    TESTING = False
    SESSION_COOKIE_SECURE = False
    
    # For development, use SQLite by default
    # Override with PostgreSQL for production simulation
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///hr_system.db'
    
    # Disable email in development
    MAIL_SUPPRESS_SEND = os.environ.get('MAIL_SUPPRESS_SEND', True)
    
    # Verbose logging in development
    SQLALCHEMY_ECHO = True
    LOG_LEVEL = 'DEBUG'


class ProductionConfig(Config):
    """Production environment configuration."""
    
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    
    # PostgreSQL database connection
    # Format: postgresql://user:password@localhost:5432/hr_system
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://hr_admin:password@localhost:5432/hr_system'
    
    # Ensure required production settings
    if not os.environ.get('SECRET_KEY'):
        raise ValueError("SECRET_KEY environment variable not set in production")
    
    if not os.environ.get('MAIL_USERNAME'):
        raise ValueError("MAIL_USERNAME environment variable not set for email")
    
    # Enable all features in production
    ENABLE_AUTO_SCREENING = True
    ENABLE_EMAIL_NOTIFICATIONS = True
    ENABLE_INTERVIEW_REMINDERS = True
    ENABLE_WEEKLY_REPORTS = True
    ENABLE_BACKGROUND_JOBS = True
    
    LOG_LEVEL = 'WARNING'


class TestingConfig(Config):
    """Testing environment configuration."""
    
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SESSION_COOKIE_SECURE = False
    
    # Disable email sending in tests
    MAIL_SUPPRESS_SEND = True
    
    # Disable rate limiting in tests
    RATE_LIMIT_ENABLED = False
    
    # Use in-memory storage for tests
    RATE_LIMIT_STORAGE = 'memory'


# Configuration dictionary for easy access
config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(config_name=None):
    """Get configuration object based on environment."""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    return config_by_name.get(config_name, config_by_name['default'])


# Environment setup helper
def setup_environment():
    """Setup required environment variables with sensible defaults."""
    
    defaults = {
        'FLASK_ENV': 'development',
        'COMPANY_NAME': 'Global Modern Business',
        'SUPPORT_EMAIL': 'support@company.com',
    }
    
    for key, value in defaults.items():
        if key not in os.environ:
            os.environ[key] = value
