# utils/__init__.py

# This file makes the utils directory a Python package
# It can be empty or contain package-level imports and initialization

from .encryption import (
    generate_encryption_key,
    encrypt_message,
    decrypt_message,
    generate_otp,
    hash_file
)

from .email_sender import (
    send_email,
    send_verification_email,
    send_async_email
)

from .file_handler import (
    allowed_file,
    get_file_type,
    save_media_file,
    generate_image_thumbnail,
    generate_video_thumbnail,
    validate_image,
    get_file_size
)

from .helpers import (
    generate_secure_filename,
    resize_image,
    format_file_size,
    is_safe_url,
    validate_email,
    validate_password,
    format_timestamp,
    calculate_relationship_days,
    generate_love_quote,
    calculate_streak_dates,
    sanitize_filename,
    get_mime_type,
    image_to_base64,
    format_duration,
    rate_limit,
    json_serializer,
    get_client_ip,
    generate_qr_code
)

# Package version
__version__ = '1.0.0'
__author__ = 'LunaLink Team'
__description__ = 'Utility functions for LunaLink application'

# You can also initialize any package-level configurations here
def init_utils(app):
    """
    Initialize utilities with Flask app context
    This function can be used to set up any utilities that need app context
    """
    # Store app reference if needed by any utility functions
    pass

# Export commonly used functions for easy access
__all__ = [
    # Encryption
    'generate_encryption_key',
    'encrypt_message',
    'decrypt_message',
    'generate_otp',
    'hash_file',
    
    # Email
    'send_email',
    'send_verification_email',
    'send_async_email',
    
    # File handling
    'allowed_file',
    'get_file_type',
    'save_media_file',
    'generate_image_thumbnail',
    'generate_video_thumbnail',
    'validate_image',
    'get_file_size',
    
    # Helpers
    'generate_secure_filename',
    'resize_image',
    'format_file_size',
    'is_safe_url',
    'validate_email',
    'validate_password',
    'format_timestamp',
    'calculate_relationship_days',
    'generate_love_quote',
    'calculate_streak_dates',
    'sanitize_filename',
    'get_mime_type',
    'image_to_base64',
    'format_duration',
    'rate_limit',
    'json_serializer',
    'get_client_ip',
    'generate_qr_code'
]