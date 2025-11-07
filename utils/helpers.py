import os
import secrets
import string
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
from PIL import Image
import io
import base64
from urllib.parse import urlparse, urljoin

def generate_secure_filename(length=32):
    """Generate a secure random filename"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def allowed_file(filename, allowed_extensions=None):
    """Check if file extension is allowed"""
    if allowed_extensions is None:
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 
                             'mp4', 'mov', 'avi', 'mkv', 'webm',
                             'mp3', 'wav', 'ogg', 'm4a'}
    
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def resize_image(image_path, max_size=(800, 800), quality=85):
    """Resize an image while maintaining aspect ratio"""
    try:
        with Image.open(image_path) as img:
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1])
                img = background
            
            # Save the resized image
            img.save(image_path, 'JPEG', quality=quality, optimize=True)
            return True
    except Exception as e:
        current_app.logger.error(f"Error resizing image {image_path}: {str(e)}")
        return False

def generate_thumbnail(image_path, thumbnail_path, size=(200, 200)):
    """Generate a thumbnail for an image"""
    try:
        with Image.open(image_path) as img:
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1])
                img = background
            
            img.save(thumbnail_path, 'JPEG', quality=80, optimize=True)
            return True
    except Exception as e:
        current_app.logger.error(f"Error generating thumbnail {thumbnail_path}: {str(e)}")
        return False

def format_file_size(size_bytes):
    """Convert file size to human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def get_file_extension(filename):
    """Get file extension from filename"""
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

def is_safe_url(target):
    """Check if URL is safe for redirects"""
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc

def validate_email(email):
    """Basic email validation"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Password strength validation"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit"
    
    return True, "Password is strong"

def format_timestamp(timestamp, format_type='relative'):
    """Format timestamp for display"""
    if format_type == 'relative':
        now = datetime.utcnow()
        diff = now - timestamp
        
        if diff < timedelta(minutes=1):
            return "Just now"
        elif diff < timedelta(hours=1):
            minutes = int(diff.total_seconds() / 60)
            return f"{minutes}m ago"
        elif diff < timedelta(days=1):
            hours = int(diff.total_seconds() / 3600)
            return f"{hours}h ago"
        elif diff < timedelta(days=7):
            days = diff.days
            return f"{days}d ago"
        else:
            return timestamp.strftime('%b %d, %Y')
    
    elif format_type == 'chat':
        now = datetime.utcnow()
        if timestamp.date() == now.date():
            return timestamp.strftime('%H:%M')
        elif timestamp.date() == (now - timedelta(days=1)).date():
            return 'Yesterday'
        else:
            return timestamp.strftime('%b %d')
    
    else:
        return timestamp.strftime('%Y-%m-%d %H:%M:%S')

def calculate_relationship_days(start_date):
    """Calculate number of days in relationship"""
    if not start_date:
        return 0
    
    today = datetime.utcnow().date()
    return (today - start_date.date()).days

def generate_love_quote():
    """Generate a random love quote"""
    quotes = [
        "Every love story is beautiful, but ours is my favorite. 💖",
        "I saw that you were perfect, and so I loved you. Then I saw that you were not perfect and I loved you even more. 🌟",
        "You are my today and all of my tomorrows. 💫",
        "I love you not only for what you are, but for what I am when I am with you. 🌹",
        "In all the world, there is no heart for me like yours. In all the world, there is no love for you like mine. 💞",
        "I need you like a heart needs a beat. 💓",
        "You are the source of my joy, the center of my world, and the whole of my heart. 🌈",
        "I choose you. And I'll choose you over and over and over. Without pause, without a doubt, in a heartbeat. I'll keep choosing you. 💌",
        "Your love is all I need to feel complete. 💕",
        "You're the missing piece to my puzzle. 🧩",
        "Loving you is like breathing, I can't stop and I don't want to. 💨",
        "You complete me in ways I never knew I was incomplete. ✨",
        "My heart is and always will be yours. 💘",
        "I never want to stop making memories with you. 📸",
        "You are my sunshine on a rainy day. ☀️"
    ]
    
    import random
    return random.choice(quotes)

def calculate_streak_dates(dates):
    """Calculate current streak from a list of dates"""
    if not dates:
        return 0
    
    # Sort dates in descending order
    dates.sort(reverse=True)
    
    current_streak = 0
    today = datetime.utcnow().date()
    expected_date = today
    
    for date in dates:
        date = date.date() if isinstance(date, datetime) else date
        
        if date == expected_date:
            current_streak += 1
            expected_date = date - timedelta(days=1)
        elif date == expected_date + timedelta(days=1):
            # Missed one day but continued next day
            current_streak += 1
            expected_date = date - timedelta(days=1)
        else:
            break
    
    return current_streak

def sanitize_filename(filename):
    """Sanitize filename to remove unsafe characters"""
    import re
    # Remove any character that's not alphanumeric, dot, hyphen, or underscore
    filename = re.sub(r'[^a-zA-Z0-9._-]', '', filename)
    # Ensure filename doesn't start with a dot
    filename = filename.lstrip('.')
    return filename

def get_mime_type(filename):
    """Get MIME type from filename"""
    mime_types = {
        'png': 'image/png',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'gif': 'image/gif',
        'bmp': 'image/bmp',
        'webp': 'image/webp',
        'mp4': 'video/mp4',
        'mov': 'video/quicktime',
        'avi': 'video/x-msvideo',
        'mkv': 'video/x-matroska',
        'webm': 'video/webm',
        'mp3': 'audio/mpeg',
        'wav': 'audio/wav',
        'ogg': 'audio/ogg',
        'm4a': 'audio/mp4'
    }
    
    ext = get_file_extension(filename)
    return mime_types.get(ext, 'application/octet-stream')

def image_to_base64(image_path):
    """Convert image to base64 string"""
    try:
        with open(image_path, 'rb') as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')
    except Exception as e:
        current_app.logger.error(f"Error converting image to base64: {str(e)}")
        return None

def format_duration(seconds):
    """Format duration in seconds to human readable format"""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes}m"
    else:
        hours = int(seconds / 3600)
        minutes = int((seconds % 3600) / 60)
        return f"{hours}h {minutes}m"

def rate_limit(key_func, limit=10, window=60):
    """Decorator for rate limiting"""
    from flask import g
    import time
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            key = key_func()
            current_time = time.time()
            
            if not hasattr(g, '_rate_limit'):
                g._rate_limit = {}
            
            if key not in g._rate_limit:
                g._rate_limit[key] = []
            
            # Remove old timestamps
            g._rate_limit[key] = [t for t in g._rate_limit[key] if current_time - t < window]
            
            if len(g._rate_limit[key]) >= limit:
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'message': f'Too many requests. Please try again in {window} seconds.'
                }), 429
            
            g._rate_limit[key].append(current_time)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def json_serializer(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

def get_client_ip():
    """Get client IP address"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0]
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    else:
        return request.remote_addr

def generate_qr_code(data, size=200):
    """Generate QR code for data"""
    try:
        import qrcode
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return f"data:image/png;base64,{base64.b64encode(buffer.read()).decode()}"
    except ImportError:
        current_app.logger.warning("QRCode library not installed")
        return None
    except Exception as e:
        current_app.logger.error(f"Error generating QR code: {str(e)}")
        return None