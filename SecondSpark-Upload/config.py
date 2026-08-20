import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
basedir = Path(__file__).resolve().parent
load_dotenv(basedir / '.env')


class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'secondspark-dev-secret-key-2026!#35C98A')
    
    # Upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max request payload
    UPLOAD_FOLDER = os.path.join(basedir, 'app', 'static', 'uploads')
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}
    ALLOWED_DOC_EXTENSIONS = {'pdf', 'zip', 'txt', 'docx', 'stl', 'step', 'ino', 'py', 'cpp', 'c', 'h'}
    
    # Session security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 86400 * 7  # 7 days

    # ── Google OAuth 2.0 & Identity Services ──────────────────────────────────
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
    GOOGLE_REDIRECT_URI = os.environ.get('GOOGLE_REDIRECT_URI', '')

    # ── Flask-Mail (Gmail SMTP) ───────────────────────────────────────────────
    MAIL_SERVER   = os.environ.get('MAIL_SERVER',  'smtp.gmail.com')
    MAIL_PORT     = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS  = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USE_SSL  = False
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'karnatihitesh@gmail.com')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'SecondSpark <karnatihitesh@gmail.com>')
    MAIL_MAX_EMAILS = None
    MAIL_ASCII_ATTACHMENTS = False
    
    # Database configuration
    # Check for MYSQL environment variables first; fallback to SQLite
    MYSQL_USER = os.environ.get('MYSQL_USER')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD')
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_PORT = os.environ.get('MYSQL_PORT', '3306')
    MYSQL_DB = os.environ.get('MYSQL_DB', 'secondspark')

    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL:
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    elif MYSQL_USER and MYSQL_PASSWORD:
        SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}?charset=utf8mb4"
    else:
        # Default zero-config fallback to SQLite
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(basedir, 'secondspark.db')}"
        
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 280,
        'pool_pre_ping': True,
    } if 'mysql' in SQLALCHEMY_DATABASE_URI else {}


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
