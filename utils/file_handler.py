import os
import uuid
from werkzeug.utils import secure_filename
from PIL import Image, ImageOps

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {
        'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp',  # Images
        'mp4', 'mov', 'avi', 'mkv', 'webm',          # Videos
        'mp3', 'wav', 'ogg', 'm4a'                   # Audio
    }
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_type(file):
    """Determine file type using file extension"""
    filename = file.filename.lower()
    
    # Image types
    image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}
    # Video types  
    video_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.webm'}
    # Audio types
    audio_extensions = {'.mp3', '.wav', '.ogg', '.m4a'}
    
    for ext in image_extensions:
        if filename.endswith(ext):
            return f'image/{ext[1:]}' if ext != '.jpg' else 'image/jpeg'
    
    for ext in video_extensions:
        if filename.endswith(ext):
            return f'video/{ext[1:]}'
    
    for ext in audio_extensions:
        if filename.endswith(ext):
            return f'audio/{ext[1:]}'
    
    return 'application/octet-stream'

def save_media_file(file, filename):
    """Save media file and generate thumbnail if needed"""
    # Create unique filename
    file_ext = filename.rsplit('.', 1)[1].lower()
    unique_filename = f"{uuid.uuid4()}.{file_ext}"
    
    # Determine file type and save path
    file_type = get_file_type(file)
    
    if file_type.startswith('image'):
        save_path = os.path.join('static/uploads/images', unique_filename)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        file.save(save_path)
        
        # Generate thumbnail for images
        thumbnail_path = generate_image_thumbnail(save_path, unique_filename)
        return save_path, thumbnail_path
        
    elif file_type.startswith('video'):
        save_path = os.path.join('static/uploads/videos', unique_filename)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        file.save(save_path)
        return save_path, None
        
    elif file_type.startswith('audio'):
        save_path = os.path.join('static/uploads/audio', unique_filename)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        file.save(save_path)
        return save_path, None
        
    else:
        save_path = os.path.join('static/uploads/files', unique_filename)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        file.save(save_path)
        return save_path, None

def generate_image_thumbnail(image_path, filename):
    """Generate thumbnail for image"""
    try:
        image = Image.open(image_path)
        image.thumbnail((200, 200), Image.Resampling.LANCZOS)
        
        thumbnail_path = os.path.join('static/uploads/thumbnails', filename)
        os.makedirs(os.path.dirname(thumbnail_path), exist_ok=True)
        
        # Convert to RGB if necessary
        if image.mode in ('RGBA', 'LA'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[-1])
            image = background
        
        # Convert to JPEG for thumbnails
        if thumbnail_path.lower().endswith(('.png', '.gif')):
            thumbnail_path = thumbnail_path.rsplit('.', 1)[0] + '.jpg'
        
        image.save(thumbnail_path, 'JPEG', quality=85)
        return thumbnail_path
    except Exception as e:
        print(f"Error generating thumbnail: {e}")
        return None

def generate_video_thumbnail(file, filename):
    """Generate thumbnail for video - placeholder implementation"""
    # In production, you could use ffmpeg or moviepy
    # For now, return a placeholder or None
    return None

def validate_image(file):
    """Validate image file"""
    try:
        image = Image.open(file)
        image.verify()
        file.seek(0)  # Reset file pointer
        return True
    except Exception as e:
        print(f"Image validation error: {e}")
        return False

def get_file_size(file_path):
    """Get file size in human-readable format"""
    try:
        size_bytes = os.path.getsize(file_path)
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        
        return f"{size_bytes:.1f} TB"
    except OSError:
        return "Unknown"