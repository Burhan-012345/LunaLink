import os
from flask import Blueprint, flash, redirect, render_template, request, jsonify, url_for
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import requests
import random

from models import Message, db, User, Anniversary, Note, Mood, ChatStreak, UserSettings

dashboard_bp = Blueprint('dashboard', __name__)

# Romantic quotes for the dashboard
ROMANTIC_QUOTES = [
    "Every love story is beautiful, but ours is my favorite. 💖",
    "I saw that you were perfect, and so I loved you. Then I saw that you were not perfect and I loved you even more. 🌟",
    "You are my today and all of my tomorrows. 💫",
    "I love you not only for what you are, but for what I am when I am with you. 🌹",
    "In all the world, there is no heart for me like yours. In all the world, there is no love for you like mine. 💞",
    "I need you like a heart needs a beat. 💓",
    "You are the source of my joy, the center of my world, and the whole of my heart. 🌈",
    "I choose you. And I'll choose you over and over and over. Without pause, without a doubt, in a heartbeat. I'll keep choosing you. 💌"
]

@dashboard_bp.route('/')
@login_required
def dashboard():
    partner = current_user.partner
    streak = ChatStreak.query.filter_by(couple_id=current_user.id).first()
    
    # Get today's romantic quote
    today_quote = random.choice(ROMANTIC_QUOTES)
    
    # Calculate relationship days if partner exists
    relationship_days = 0
    if partner and current_user.created_at:
        start_date = min(current_user.created_at, partner.created_at)
        relationship_days = (datetime.utcnow().date() - start_date.date()).days
    
    # Get upcoming anniversaries
    upcoming_anniversaries = []
    if partner:
        anniversaries = Anniversary.query.filter_by(couple_id=current_user.id).all()
        today = datetime.utcnow().date()
        
        for anniv in anniversaries:
            next_date = anniv.date.replace(year=today.year)
            if next_date < today:
                next_date = next_date.replace(year=today.year + 1)
            
            days_until = (next_date - today).days
            upcoming_anniversaries.append({
                'title': anniv.title,
                'date': anniv.date,
                'days_until': days_until,
                'next_date': next_date
            })
        
        # Sort by days until
        upcoming_anniversaries.sort(key=lambda x: x['days_until'])
    
    # Get recent moods
    recent_moods = Mood.query.filter_by(user_id=current_user.id).order_by(
        Mood.created_at.desc()
    ).limit(5).all()
    
    # Get shared notes
    shared_notes = Note.query.filter_by(
        couple_id=current_user.id, 
        is_shared=True
    ).order_by(Note.updated_at.desc()).limit(5).all()
    
    return render_template('dashboard/dashboard.html',
                         partner=partner,
                         streak=streak,
                         today_quote=today_quote,
                         relationship_days=relationship_days,
                         upcoming_anniversaries=upcoming_anniversaries[:3],
                         recent_moods=recent_moods,
                         shared_notes=shared_notes)

@dashboard_bp.route('/memories')
@login_required
def memories():
    partner = current_user.partner
    if not partner:
        return render_template('dashboard/memories.html', memories=[])
    
    # Get all messages between the couple (for memory timeline)
    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == partner.id)) |
        ((Message.sender_id == partner.id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.timestamp.desc()).limit(100).all()
    
    memories_data = []
    for msg in messages:
        if not msg.is_deleted:
            memory = {
                'id': msg.id,
                'type': 'message',
                'content': msg.content,
                'timestamp': msg.timestamp,
                'sender': msg.sender.name,
                'sender_avatar': msg.sender.avatar
            }
            
            if msg.media:
                memory['type'] = 'media'
                memory['media'] = {
                    'file_path': msg.media[0].file_path,
                    'file_type': msg.media[0].file_type
                }
            
            memories_data.append(memory)
    
    return render_template('dashboard/memories.html', memories=memories_data)

@dashboard_bp.route('/notes')
@login_required
def notes():
    notes = Note.query.filter_by(couple_id=current_user.id).order_by(
        Note.updated_at.desc()
    ).all()
    
    return render_template('dashboard/notes.html', notes=notes)

@dashboard_bp.route('/add-note', methods=['POST'])
@login_required
def add_note():
    title = request.json.get('title', '')
    content = request.json.get('content', '')
    is_shared = request.json.get('is_shared', True)
    
    if not content:
        return jsonify({'error': 'Note content is required'}), 400
    
    new_note = Note(
        couple_id=current_user.id,
        title=title,
        content=content,
        is_shared=is_shared
    )
    
    db.session.add(new_note)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'note': {
            'id': new_note.id,
            'title': new_note.title,
            'content': new_note.content,
            'is_shared': new_note.is_shared,
            'created_at': new_note.created_at.isoformat()
        }
    })

@dashboard_bp.route('/update-note/<int:note_id>', methods=['PUT'])
@login_required
def update_note(note_id):
    note = Note.query.get_or_404(note_id)
    
    if note.couple_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    title = request.json.get('title', note.title)
    content = request.json.get('content', note.content)
    is_shared = request.json.get('is_shared', note.is_shared)
    
    note.title = title
    note.content = content
    note.is_shared = is_shared
    note.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({'success': True})

@dashboard_bp.route('/delete-note/<int:note_id>', methods=['DELETE'])
@login_required
def delete_note(note_id):
    note = Note.query.get_or_404(note_id)
    
    if note.couple_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    db.session.delete(note)
    db.session.commit()
    
    return jsonify({'success': True})

@dashboard_bp.route('/add-mood', methods=['POST'])
@login_required
def add_mood():
    mood_text = request.json.get('mood_text', '')
    emoji = request.json.get('emoji', '💖')
    
    if not mood_text:
        return jsonify({'error': 'Mood text is required'}), 400
    
    new_mood = Mood(
        user_id=current_user.id,
        mood_text=mood_text,
        emoji=emoji
    )
    
    db.session.add(new_mood)
    db.session.commit()
    
    # Notify partner via SocketIO if online
    partner = current_user.partner
    if partner:
        from app import socketio
        socketio.emit('mood_update', {
            'user_id': current_user.id,
            'user_name': current_user.name,
            'mood': mood_text,
            'emoji': emoji,
            'timestamp': new_mood.created_at.isoformat()
        }, room=f'user_{partner.id}')
    
    return jsonify({
        'success': True,
        'mood': {
            'id': new_mood.id,
            'mood_text': new_mood.mood_text,
            'emoji': new_mood.emoji,
            'created_at': new_mood.created_at.isoformat()
        }
    })

@dashboard_bp.route('/add-anniversary', methods=['POST'])
@login_required
def add_anniversary():
    title = request.json.get('title', '')
    date_str = request.json.get('date', '')
    recurring = request.json.get('recurring', True)
    
    if not title or not date_str:
        return jsonify({'error': 'Title and date are required'}), 400
    
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400
    
    new_anniversary = Anniversary(
        couple_id=current_user.id,
        title=title,
        date=date,
        recurring=recurring
    )
    
    db.session.add(new_anniversary)
    db.session.commit()
    
    return jsonify({'success': True})

# Add these routes to your existing dashboard_routes.py

@dashboard_bp.route('/profile')
@login_required
def profile():
    return render_template('dashboard/profile.html')

@dashboard_bp.route('/settings')
@login_required
def settings():
    return render_template('dashboard/settings.html')

@dashboard_bp.route('/update-profile', methods=['POST'])
@login_required
def update_profile():
    if request.content_type.startswith('application/json'):
        # JSON data for profile updates
        data = request.get_json()
        current_user.name = data.get('name', current_user.name)
        current_user.status_message = data.get('status_message', current_user.status_message)
    else:
        # Form data for avatar upload
        if 'avatar' in request.files:
            file = request.files['avatar']
            if file and allowed_file(file.filename):
                filename = secure_filename(f"{current_user.id}_{file.filename}")
                file_path = os.path.join('static/images/avatars', filename)
                file.save(file_path)
                current_user.avatar = filename
    
    db.session.commit()
    return jsonify({'success': True, 'avatar_url': url_for('static', filename='images/avatars/' + current_user.avatar)})

@dashboard_bp.route('/reset-avatar', methods=['POST'])
@login_required
def reset_avatar():
    current_user.avatar = 'default_avatar.png'
    db.session.commit()
    return jsonify({'success': True, 'avatar_url': url_for('static', filename='images/avatars/default_avatar.png')})

@dashboard_bp.route('/get-settings')
@login_required
def get_settings():
    settings = UserSettings.query.filter_by(user_id=current_user.id).first()
    if settings:
        return jsonify({
            'success': True,
            'settings': {
                'theme': settings.theme,
                'wallpaper': settings.wallpaper,
                'notificationsEnabled': settings.notifications_enabled,
                'soundsEnabled': settings.sounds_enabled,
                'emailNotifications': settings.email_notifications,  # ADD THIS
                'musicEnabled': settings.music_enabled,
                'showOnlineStatus': settings.show_online_status,
                'readReceipts': settings.read_receipts,
                'typingIndicators': settings.typing_indicators,
                'sessionTimeout': settings.session_timeout,
                'language': settings.language,
                'timezone': settings.timezone,
                'dateFormat': settings.date_format
            }
        })
    return jsonify({'success': False, 'error': 'Settings not found'})

@dashboard_bp.route('/update-settings', methods=['POST'])
@login_required
def update_settings():
    data = request.get_json()
    settings = UserSettings.query.filter_by(user_id=current_user.id).first()
    
    if not settings:
        settings = UserSettings(user_id=current_user.id)
        db.session.add(settings)
    
    # Update settings
    settings.theme = data.get('theme', settings.theme)
    settings.wallpaper = data.get('wallpaper', settings.wallpaper)
    settings.notifications_enabled = data.get('notificationsEnabled', settings.notifications_enabled)
    settings.sounds_enabled = data.get('soundsEnabled', settings.sounds_enabled)
    settings.email_notifications = data.get('emailNotifications', settings.email_notifications)  # ADD THIS
    settings.music_enabled = data.get('musicEnabled', settings.music_enabled)
    
    # Privacy settings
    settings.show_online_status = data.get('showOnlineStatus', settings.show_online_status)
    settings.read_receipts = data.get('readReceipts', settings.read_receipts)
    settings.typing_indicators = data.get('typingIndicators', settings.typing_indicators)
    settings.session_timeout = data.get('sessionTimeout', settings.session_timeout)
    
    # Account settings
    settings.language = data.get('language', settings.language)
    settings.timezone = data.get('timezone', settings.timezone)
    settings.date_format = data.get('dateFormat', settings.date_format)
    
    db.session.commit()
    return jsonify({'success': True})

@dashboard_bp.route('/delete-account', methods=['DELETE'])
@login_required
def delete_account():
    try:
        # Delete user data (you might want to soft delete instead)
        db.session.delete(current_user)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@dashboard_bp.route('/clear-data', methods=['DELETE'])
@login_required
def clear_data():
    try:
        # Delete user's messages, media, etc.
        Message.query.filter(
            (Message.sender_id == current_user.id) | 
            (Message.receiver_id == current_user.id)
        ).delete()
        
        # Delete other user data
        Note.query.filter_by(couple_id=current_user.id).delete()
        Mood.query.filter_by(user_id=current_user.id).delete()
        Anniversary.query.filter_by(couple_id=current_user.id).delete()
        
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@dashboard_bp.route('/remove-partner', methods=['DELETE'])
@login_required
def remove_partner():
    try:
        if current_user.partner:
            # Remove partner connection
            partner_id = current_user.partner.id
            current_user.partner = None
            
            # Also remove from partner's side
            partner = User.query.get(partner_id)
            if partner:
                partner.partner = None
            
            db.session.commit()
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'No partner connected'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@dashboard_bp.route('/virtual-hug', methods=['POST'])
@login_required
def send_virtual_hug():
    partner = current_user.partner
    if not partner:
        return jsonify({'error': 'No partner linked'}), 400
    
    # Send virtual hug notification to partner
    from app import socketio
    socketio.emit('virtual_hug', {
        'from_user_id': current_user.id,
        'from_user_name': current_user.name,
        'timestamp': datetime.utcnow().isoformat()
    }, room=f'user_{partner.id}')
    
    return jsonify({'success': True, 'message': 'Virtual hug sent! 💞'})