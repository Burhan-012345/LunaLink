from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from functools import wraps

from models import db, User, Message, Media

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Simple admin check - in production, use proper role-based access
        if not current_user.is_authenticated or current_user.email != 'admin@lunalink.app':
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@login_required
@admin_required
def admin_dashboard():
    # Statistics
    total_users = User.query.count()
    total_messages = Message.query.count()
    total_media = Media.query.count()
    today_messages = Message.query.filter(
        Message.timestamp >= datetime.utcnow().date()
    ).count()
    
    # Recent activity
    recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
    recent_messages = Message.query.order_by(Message.timestamp.desc()).limit(20).all()
    
    return render_template('admin/admin.html',
                         total_users=total_users,
                         total_messages=total_messages,
                         total_media=total_media,
                         today_messages=today_messages,
                         recent_users=recent_users,
                         recent_messages=recent_messages)

@admin_bp.route('/users')
@login_required
@admin_required
def manage_users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/messages')
@login_required
@admin_required
def manage_messages():
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    messages = Message.query.order_by(Message.timestamp.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/messages.html', messages=messages)

@admin_bp.route('/backup')
@login_required
@admin_required
def backup_database():
    # Simple backup functionality
    backup_file = f"backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.db"
    
    # In production, implement proper database backup
    import shutil
    shutil.copy2('instance/lunalink.db', f'backups/{backup_file}')
    
    return jsonify({'success': True, 'backup_file': backup_file})