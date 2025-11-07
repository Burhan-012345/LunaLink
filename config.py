import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///lunalink.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Email Configuration
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'devil160907@gmail.com'
    MAIL_PASSWORD = 'zmvp pvxe ctfm ubwi'  # Replace with App Password if needed
    MAIL_DEFAULT_SENDER = 'devil160907@gmail.com'
    
    # Debug Settings - UPDATED
    DEBUG = True
    PRINT_EMAILS_TO_CONSOLE = False  # Changed from True to False
    
    # Security
    OTP_EXPIRY_MINUTES = 5
    MAX_LOGIN_ATTEMPTS = 3
    SESSION_TIMEOUT_MINUTES = 30
    
    # File Upload
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = 'static/uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'mp3', 'wav'}
    
    # Encryption
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY') or 'your-encryption-key-32-bytes'