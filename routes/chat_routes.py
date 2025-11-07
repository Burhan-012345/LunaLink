from flask import Blueprint, render_template, request, jsonify, send_file
from flask_login import login_required, current_user
from flask_socketio import emit
from datetime import datetime, timedelta
import os
from werkzeug.utils import secure_filename

from models import db, Message, Media, User
from utils.email_sender import send_invitation_email, test_email_configuration
from utils.file_handler import allowed_file, save_media_file, generate_image_thumbnail

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/')
@login_required
def chat_room():
    partner = current_user.partner
    if not partner:
        return render_template('chat/chat.html', partner=None, messages=[])
    
    # Get last 50 messages
    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == partner.id)) |
        ((Message.sender_id == partner.id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.timestamp.asc()).limit(50).all()
    
    # Mark messages as read
    unread_messages = Message.query.filter_by(
        receiver_id=current_user.id, 
        sender_id=partner.id, 
        is_read=False
    ).all()
    
    for msg in unread_messages:
        msg.is_read = True
    
    db.session.commit()
    
    return render_template('chat/chat.html', partner=partner, messages=messages)

@chat_bp.route('/send-message', methods=['POST'])
@login_required
def send_message():
    partner = current_user.partner
    if not partner:
        return jsonify({'error': 'No partner linked'}), 400
    
    content = request.form.get('message')
    message_type = request.form.get('type', 'text')
    
    if not content and 'file' not in request.files:
        return jsonify({'error': 'No content provided'}), 400
    
    new_message = Message(
        sender_id=current_user.id,
        receiver_id=partner.id,
        content=content,
        message_type=message_type,
        timestamp=datetime.utcnow()
    )
    
    # Handle file upload
    if 'file' in request.files:
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path, thumbnail_path = save_media_file(file, filename)
            
            media = Media(
                message=new_message,
                file_path=file_path,
                file_type=file.content_type,
                file_size=os.path.getsize(file_path),
                thumbnail_path=thumbnail_path
            )
            db.session.add(media)
    
    db.session.add(new_message)
    db.session.commit()
    
    # Emit SocketIO event
    message_data = {
        'id': new_message.id,
        'sender_id': current_user.id,
        'sender_name': current_user.name,
        'content': content,
        'type': message_type,
        'timestamp': new_message.timestamp.isoformat(),
        'avatar': current_user.avatar
    }
    
    emit('new_message', message_data, room=f'user_{partner.id}', namespace='/')
    
    return jsonify({'success': True, 'message': message_data})

@chat_bp.route('/messages')
@login_required
def get_messages():
    partner_id = request.args.get('partner_id')
    if not partner_id:
        return jsonify({'error': 'Partner ID required'}), 400
    
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == partner_id)) |
        ((Message.sender_id == partner_id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.timestamp.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    messages_data = []
    for msg in messages.items[::-1]:  # Reverse to get chronological order
        message_data = {
            'id': msg.id,
            'sender_id': msg.sender_id,
            'sender_name': msg.sender.name,
            'content': msg.content,
            'type': msg.message_type,
            'timestamp': msg.timestamp.isoformat(),
            'is_read': msg.is_read,
            'avatar': msg.sender.avatar
        }
        
        if msg.media:
            media = msg.media[0]
            message_data['media'] = {
                'file_path': media.file_path,
                'file_type': media.file_type,
                'thumbnail_path': media.thumbnail_path
            }
        
        messages_data.append(message_data)
    
    return jsonify({
        'messages': messages_data,
        'has_next': messages.has_next,
        'has_prev': messages.has_prev
    })

@chat_bp.route('/media')
@login_required
def get_media():
    partner = current_user.partner
    if not partner:
        return jsonify({'error': 'No partner linked'}), 400
    
    media_messages = Message.query.join(Media).filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == partner.id)) |
        ((Message.sender_id == partner.id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.timestamp.desc()).all()
    
    media_data = []
    for msg in media_messages:
        if msg.media:
            for media in msg.media:
                media_data.append({
                    'id': media.id,
                    'message_id': msg.id,
                    'file_path': media.file_path,
                    'file_type': media.file_type,
                    'thumbnail_path': media.thumbnail_path,
                    'timestamp': msg.timestamp.isoformat(),
                    'sender_name': msg.sender.name
                })
    
    return jsonify({'media': media_data})

@chat_bp.route('/download/<int:media_id>')
@login_required
def download_media(media_id):
    media = Media.query.get_or_404(media_id)
    
    # Check if user has permission to access this media
    if media.message.sender_id != current_user.id and media.message.receiver_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    return send_file(media.file_path, as_attachment=True)

@chat_bp.route('/delete-message/<int:message_id>', methods=['DELETE'])
@login_required
def delete_message(message_id):
    message = Message.query.get_or_404(message_id)
    
    if message.sender_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    message.is_deleted = True
    db.session.commit()
    
    return jsonify({'success': True})

@chat_bp.route('/send-invitation', methods=['POST'])
@login_required
def send_invitation():
    email = request.json.get('email')
    
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    
    # Validate email format
    import re
    if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
        return jsonify({'error': 'Invalid email format'}), 400
    
    try:
        print(f"📧 Attempting to send invitation to: {email}")
        
        # Send invitation email
        success = send_invitation_email(
            to_email=email,
            inviter_name=current_user.name,
            inviter_email=current_user.email
        )
        
        if success:
            print(f"✓ Invitation sent successfully to: {email}")
            return jsonify({'success': True, 'message': 'Invitation sent successfully!'})
        else:
            print(f"❌ Failed to send invitation to: {email}")
            return jsonify({'error': 'Failed to send invitation. Please check email configuration.'}), 500
    
    except Exception as e:
        print(f"❌ Error sending invitation: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return jsonify({'error': 'An unexpected error occurred. Please try again.'}), 500
    
@chat_bp.route('/test-email', methods=['GET'])
@login_required
def test_email():
    """
    Test email configuration and sending
    """
    try:
        success = test_email_configuration()
        if success:
            return jsonify({'success': True, 'message': 'Email test completed successfully!'})
        else:
            return jsonify({'error': 'Email test failed. Check server logs for details.'}), 500
    except Exception as e:
        return jsonify({'error': f'Email test error: {str(e)}'}), 500
    
@chat_bp.route('/debug-email')
def debug_email():
    from flask import current_app
    config_info = {
        'MAIL_SERVER': current_app.config.get('MAIL_SERVER'),
        'MAIL_PORT': current_app.config.get('MAIL_PORT'),
        'MAIL_USERNAME': current_app.config.get('MAIL_USERNAME'),
        'MAIL_PASSWORD': '***' if current_app.config.get('MAIL_PASSWORD') else None,
        'MAIL_DEFAULT_SENDER': current_app.config.get('MAIL_DEFAULT_SENDER')
    }
    return jsonify(config_info)

@chat_bp.route('/typing', methods=['POST'])
@login_required
def typing():
    partner = current_user.partner
    if not partner:
        return jsonify({'error': 'No partner linked'}), 400
    
    is_typing = request.json.get('typing', False)
    
    emit('user_typing', {
        'user_id': current_user.id,
        'user_name': current_user.name,
        'typing': is_typing
    }, room=f'user_{partner.id}', namespace='/')
    
    return jsonify({'success': True})