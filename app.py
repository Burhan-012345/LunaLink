import os
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, join_room
from flask_login import LoginManager, current_user, login_required
from flask_mail import Mail
from datetime import datetime, timedelta
import logging
import re

from config import Config
from models import Anniversary, Mood, Note, db, User, Message, UserSettings, OTP
from utils.encryption import encrypt_message, decrypt_message

# Try to import email_sender from utils
try:
    from utils.email_sender import send_verification_email, check_email_config, get_last_otp, print_email_status, test_email_configuration
    email_sender_available = True
except ImportError as e:
    print(f"⚠️  email_sender not found in utils: {e}")
    email_sender_available = False

# Initialize extensions first (outside create_app)
socketio = SocketIO()
mail = Mail()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions with app
    db.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")
    mail.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    
    # Register blueprints
    from routes.auth_routes import auth_bp
    from routes.chat_routes import chat_bp
    from routes.dashboard_routes import dashboard_bp
    from routes.admin_routes import admin_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(chat_bp, url_prefix='/chat')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return render_template('dashboard/dashboard.html')
        return render_template('index.html')
    
    # =========================================================================
    # EMAIL DEBUGGING ROUTES (Updated for utils folder)
    # =========================================================================
    
    @app.route('/debug/email-status')
    def debug_email_status():
        """Comprehensive email system status check"""
        try:
            # Check if email_sender is available
            if not email_sender_available:
                return jsonify({
                    'error': 'email_sender module not found in utils folder',
                    'email_sender_available': False,
                    'debug_mode': app.config.get('DEBUG', False),
                    'mail_server': app.config.get('MAIL_SERVER'),
                    'mail_username': app.config.get('MAIL_USERNAME'),
                    'current_time': datetime.utcnow().isoformat()
                })
            
            # Check configuration
            config_ok = check_email_config()
            
            # Get last OTP info
            last_otp_info = get_last_otp()
            
            # Check recent OTPs from database
            recent_otps = OTP.query.order_by(OTP.created_at.desc()).limit(5).all()
            otp_list = []
            for otp in recent_otps:
                otp_list.append({
                    'email': otp.email,
                    'otp_code': otp.otp_code,
                    'purpose': otp.purpose,
                    'created_at': otp.created_at.isoformat(),
                    'expires_at': otp.expires_at.isoformat(),
                    'is_used': otp.is_used,
                    'is_expired': otp.is_expired()
                })
            
            return jsonify({
                'email_system_configured': config_ok,
                'email_sender_available': True,
                'debug_mode': app.config.get('DEBUG', False),
                'print_emails_to_console': app.config.get('PRINT_EMAILS_TO_CONSOLE', True),
                'mail_server': app.config.get('MAIL_SERVER'),
                'mail_port': app.config.get('MAIL_PORT'),
                'mail_username': app.config.get('MAIL_USERNAME'),
                'mail_use_tls': app.config.get('MAIL_USE_TLS'),
                'last_otp_info': last_otp_info,
                'recent_otps': otp_list,
                'current_time': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            return jsonify({
                'error': f'Error checking email status: {str(e)}',
                'current_time': datetime.utcnow().isoformat()
            }), 500

    @app.route('/debug/send-test-otp', methods=['POST'])
    def debug_send_test_otp():
        """Send a test OTP email to verify the system"""
        try:
            if not email_sender_available:
                return jsonify({
                    'success': False,
                    'error': 'email_sender module not available in utils folder'
                }), 500
                
            data = request.get_json()
            test_email = data.get('email', 'test@example.com')
            test_name = data.get('name', 'Test User')
            
            from datetime import datetime, timedelta
            
            # Generate test OTP
            import random
            test_otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            
            # Create OTP record
            test_otp_record = OTP(
                email=test_email,
                otp_code=test_otp,
                purpose='verification',
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(minutes=10)
            )
            
            db.session.add(test_otp_record)
            db.session.commit()
            
            # Send test email
            success = send_verification_email(
                email=test_email,
                otp_code=test_otp,
                name=test_name,
                purpose='verification'
            )
            
            return jsonify({
                'success': success,
                'test_otp': test_otp,
                'test_email': test_email,
                'test_name': test_name,
                'message': 'Check console for email output and OTP details',
                'otp_record_id': test_otp_record.id,
                'expires_at': test_otp_record.expires_at.isoformat()
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Error sending test OTP: {str(e)}'
            }), 500

    @app.route('/debug/email-config')
    def debug_email_config():
        """Display current email configuration (safe version)"""
        config_info = {
            'MAIL_SERVER': app.config.get('MAIL_SERVER'),
            'MAIL_PORT': app.config.get('MAIL_PORT'),
            'MAIL_USE_TLS': app.config.get('MAIL_USE_TLS'),
            'MAIL_USERNAME': app.config.get('MAIL_USERNAME'),
            'MAIL_PASSWORD': '***' if app.config.get('MAIL_PASSWORD') else 'Not set',
            'MAIL_DEFAULT_SENDER': app.config.get('MAIL_DEFAULT_SENDER'),
            'DEBUG': app.config.get('DEBUG'),
            'PRINT_EMAILS_TO_CONSOLE': app.config.get('PRINT_EMAILS_TO_CONSOLE', True),
            'SECRET_KEY_SET': bool(app.config.get('SECRET_KEY')),
            'DATABASE_URL': app.config.get('SQLALCHEMY_DATABASE_URI', 'Not set'),
            'EMAIL_SENDER_AVAILABLE': email_sender_available
        }
        
        return jsonify(config_info)

    @app.route('/debug/last-otp')
    def debug_last_otp():
        """Get the last OTP that was generated"""
        try:
            if not email_sender_available:
                return jsonify({
                    'error': 'email_sender module not available',
                    'email_sender_available': False
                })
            
            # Also check database for recent OTPs
            recent_otp = OTP.query.order_by(OTP.created_at.desc()).first()
            recent_otp_info = None
            if recent_otp:
                recent_otp_info = {
                    'email': recent_otp.email,
                    'otp_code': recent_otp.otp_code,
                    'purpose': recent_otp.purpose,
                    'created_at': recent_otp.created_at.isoformat(),
                    'expires_at': recent_otp.expires_at.isoformat(),
                    'is_used': recent_otp.is_used,
                    'is_expired': recent_otp.is_expired()
                }
            
            return jsonify({
                'file_otp': get_last_otp(),
                'database_otp': recent_otp_info,
                'current_time': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            return jsonify({
                'error': f'Error getting last OTP: {str(e)}'
            }), 500

    @app.route('/debug/test-email-connection', methods=['POST'])
    def debug_test_email_connection():
        """Test email connection and sending capability"""
        try:
            if not email_sender_available:
                return jsonify({
                    'success': False,
                    'error': 'email_sender module not available in utils folder'
                }), 500
            
            success = test_email_configuration()
            
            return jsonify({
                'success': success,
                'message': 'Email configuration test completed - check console for details'
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Error testing email connection: {str(e)}'
            }), 500

    @app.route('/debug/clear-otps', methods=['POST'])
    def debug_clear_otps():
        """Clear all OTPs from database (for testing)"""
        try:
            # Delete all OTPs
            OTP.query.delete()
            db.session.commit()
            
            # Also clear the last_otp.txt file
            try:
                if os.path.exists('last_otp.txt'):
                    os.remove('last_otp.txt')
            except:
                pass
            
            return jsonify({
                'success': True,
                'message': 'All OTPs cleared from database and file'
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'error': f'Error clearing OTPs: {str(e)}'
            }), 500

    # =========================================================================
    # EXISTING EMAIL ROUTES (Enhanced with debugging)
    # =========================================================================
    
    @app.route('/chat/email-status')
    @login_required
    def email_status():
        """Check if email configuration is properly set up"""
        try:
            # Check required email configurations
            required_configs = ['MAIL_SERVER', 'MAIL_PORT', 'MAIL_USERNAME', 'MAIL_PASSWORD', 'MAIL_DEFAULT_SENDER']
            missing_configs = []
            
            for config in required_configs:
                if not app.config.get(config):
                    missing_configs.append(config)
            
            # If all configs are present, try to test the connection
            can_connect = False
            if not missing_configs:
                try:
                    # Simple test to see if we can create a message
                    from flask_mail import Message
                    msg = Message(
                        subject="Test",
                        sender=app.config['MAIL_DEFAULT_SENDER'],
                        recipients=["test@example.com"]
                    )
                    msg.body = "Test message"
                    can_connect = True
                except Exception as e:
                    missing_configs.append(f"Configuration error: {str(e)}")
            
            return jsonify({
                'configured': len(missing_configs) == 0 and can_connect,
                'missing_configs': missing_configs,
                'debug_mode': app.config.get('DEBUG', False),
                'print_to_console': app.config.get('PRINT_EMAILS_TO_CONSOLE', True)
            })
            
        except Exception as e:
            return jsonify({
                'configured': False,
                'missing_configs': [f'Error: {str(e)}']
            }), 500

    @app.route('/chat/send-test-email', methods=['POST'])
    @login_required
    def send_test_email():
        """Send a test email to verify email functionality"""
        try:
            data = request.get_json()
            test_email = data.get('test_email')
            
            if not test_email:
                return jsonify({'success': False, 'error': 'No email address provided'})
            
            # Validate email format
            if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', test_email):
                return jsonify({'success': False, 'error': 'Invalid email address format'})
            
            # Create test email message
            from flask_mail import Message
            
            msg = Message(
                subject="LunaLink - Email Configuration Test ✅",
                sender=app.config['MAIL_DEFAULT_SENDER'],
                recipients=[test_email]
            )
            
            msg.html = f"""
            <h1>Email Test Successful! 🎉</h1>
            <p>If you're reading this, your LunaLink email configuration is working perfectly!</p>
            <p><strong>Configuration Details:</strong></p>
            <ul>
                <li>Server: {app.config.get('MAIL_SERVER', 'N/A')}</li>
                <li>Port: {app.config.get('MAIL_PORT', 'N/A')}</li>
                <li>Sender: {app.config.get('MAIL_DEFAULT_SENDER', 'N/A')}</li>
                <li>Debug Mode: {app.config.get('DEBUG', 'N/A')}</li>
            </ul>
            <p>You can now send invitation emails to your partner!</p>
            <p><em>Sent to: {test_email}</em></p>
            """
            
            msg.body = f"""
            Email Test Successful! 🎉
            
            If you're reading this, your LunaLink email configuration is working perfectly!
            
            Configuration Details:
            - Server: {app.config.get('MAIL_SERVER', 'N/A')}
            - Port: {app.config.get('MAIL_PORT', 'N/A')}
            - Sender: {app.config.get('MAIL_DEFAULT_SENDER', 'N/A')}
            - Debug Mode: {app.config.get('DEBUG', 'N/A')}
            
            You can now send invitation emails to your partner!
            
            Sent to: {test_email}
            """
            
            # Send email
            mail.send(msg)
            
            return jsonify({
                'success': True,
                'message': f'Test email sent successfully to {test_email}'
            })
            
        except Exception as e:
            logging.error(f"Error sending test email: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'Failed to send test email: {str(e)}'
            }), 500

    @app.route('/chat/send-invitation', methods=['POST'])
    @login_required
    def send_invitation():
        """Send partner invitation email"""
        try:
            data = request.get_json()
            email = data.get('email')
            
            if not email:
                return jsonify({'success': False, 'error': 'No email address provided'})
            
            # Validate email format
            if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
                return jsonify({'success': False, 'error': 'Invalid email address format'})
            
            # Create invitation email
            from flask_mail import Message
            
            invitation_link = f"{request.host_url}auth/register?invite={current_user.id}"
            
            msg = Message(
                subject=f"Join LunaLink - {current_user.name} Invited You! 💞",
                sender=app.config['MAIL_DEFAULT_SENDER'],
                recipients=[email]
            )
            
            msg.html = f"""
            <h1>You're Invited to Join LunaLink! 💌</h1>
            
            <p>Hello there!</p>
            
            <p><strong>{current_user.name}</strong> ({current_user.email}) has invited you to join 
            <strong>LunaLink</strong>, the private couple messaging app designed to strengthen your connection.</p>
            
            <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0;">
                <h3 style="margin-top: 0;">With LunaLink, you can:</h3>
                <ul>
                    <li>💌 Send private messages to your partner</li>
                    <li>📸 Share photos and media securely</li>
                    <li>🎵 Share background music and moods</li>
                    <li>❤️ Strengthen your relationship through dedicated communication</li>
                </ul>
            </div>
            
            <p>
                <a href="{invitation_link}" style="background: #4a90e2; color: white; padding: 12px 24px; 
                text-decoration: none; border-radius: 6px; display: inline-block; font-weight: bold;">
                    Accept Invitation & Join LunaLink
                </a>
            </p>
            
            <p>Or copy this link: <code>{invitation_link}</code></p>
            
            <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
            
            <p style="color: #666; font-size: 14px;">
                This invitation was sent by {current_user.name}.<br>
                If you believe you received this in error, please ignore this email.
            </p>
            """
            
            msg.body = f"""
            💌 You're Invited to Join LunaLink!
            
            Hello there!
            
            {current_user.name} ({current_user.email}) has invited you to join LunaLink, 
            the private couple messaging app designed to strengthen your connection.
            
            With LunaLink, you can:
            • 💌 Send private messages to your partner
            • 📸 Share photos and media securely
            • 🎵 Share background music and moods
            • ❤️ Strengthen your relationship through dedicated communication
            
            Click here to accept the invitation and join:
            {invitation_link}
            
            If you have any questions, feel free to reply to this email.
            
            With love,
            The LunaLink Team 💕
            
            This invitation was sent by {current_user.name}. 
            If you believe you received this in error, please ignore this email.
            """
            
            # Send email
            mail.send(msg)
            
            return jsonify({
                'success': True,
                'message': f'Invitation sent successfully to {email}'
            })
            
        except Exception as e:
            logging.error(f"Error sending invitation email: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'Failed to send invitation: {str(e)}'
            }), 500
    
    @app.errorhandler(404)
    def not_found(error):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('500.html'), 500
    
    return app

# SocketIO Events
@socketio.on('connect')
@login_required
def handle_connect():
    if current_user.is_authenticated:
        join_room(f'user_{current_user.id}')
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
        
        # Notify partner if connected
        if current_user.partner:
            emit('user_online', {
                'user_id': current_user.id, 
                'status': 'online',
                'user_name': current_user.name
            }, room=f'user_{current_user.partner.id}')
        
        emit('user_online', {'user_id': current_user.id, 'status': 'online'}, broadcast=True)

@socketio.on('disconnect')
@login_required
def handle_disconnect():
    current_user.last_seen = datetime.utcnow()
    db.session.commit()
    emit('user_offline', {'user_id': current_user.id, 'status': 'offline'}, broadcast=True)

@socketio.on('send_message')
@login_required
def handle_send_message(data):
    try:
        partner = current_user.partner
        if not partner:
            emit('error', {'message': 'No partner linked'})
            return
        
        encrypted_content = encrypt_message(data['message'])
        
        new_message = Message(
            sender_id=current_user.id,
            receiver_id=partner.id,
            content=data['message'],
            encrypted_content=encrypted_content,
            message_type=data.get('type', 'text')
        )
        
        db.session.add(new_message)
        db.session.commit()
        
        # Update chat streak
        update_chat_streak(current_user.id)
        
        message_data = {
            'id': new_message.id,
            'sender_id': current_user.id,
            'content': data['message'],
            'timestamp': new_message.timestamp.isoformat(),
            'type': new_message.message_type
        }
        
        emit('new_message', message_data, room=f'user_{partner.id}')
        emit('message_sent', message_data)
        
    except Exception as e:
        emit('error', {'message': 'Failed to send message'})
        logging.error(f"Message send error: {str(e)}")

@socketio.on('typing')
@login_required
def handle_typing(data):
    partner = current_user.partner
    if partner:
        emit('user_typing', {
            'user_id': current_user.id,
            'user_name': current_user.name
        }, room=f'user_{partner.id}')

@socketio.on('stop_typing')
@login_required
def handle_stop_typing(data):
    partner = current_user.partner
    if partner:
        emit('user_stop_typing', {'user_id': current_user.id}, room=f'user_{partner.id}')

@socketio.on('partner_connected')
@login_required
def handle_partner_connected(data):
    """Notify when partners are connected"""
    partner = current_user.partner
    if partner:
        emit('partner_connected', {
            'partner_id': partner.id,
            'partner_name': partner.name,
            'message': f'You are now connected with {partner.name}!'
        }, room=f'user_{current_user.id}')

def connect_users_automatically(inviter_id, new_user):
    """Automatically connect two users when invitation is accepted"""
    try:
        inviter = User.query.get(inviter_id)
        if not inviter:
            return False
        
        # Connect the users as partners
        inviter.partner_id = new_user.id
        new_user.partner_id = inviter.id
        
        # Create a welcome message
        welcome_message = Message(
            sender_id=inviter.id,
            receiver_id=new_user.id,
            content=f"Welcome to our chat, {new_user.name}! 🎉 I'm so glad you joined me on LunaLink! 💕",
            message_type='text'
        )
        
        db.session.add(welcome_message)
        db.session.commit()
        
        # Notify both users via SocketIO
        socketio.emit('partner_connected', {
            'partner_id': new_user.id,
            'partner_name': new_user.name,
            'message': f'You are now connected with {new_user.name}!'
        }, room=f'user_{inviter.id}')
        
        socketio.emit('partner_connected', {
            'partner_id': inviter.id,
            'partner_name': inviter.name,
            'message': f'You are now connected with {inviter.name}!'
        }, room=f'user_{new_user.id}')
        
        logging.info(f"Automatically connected {inviter.name} with {new_user.name}")
        print(f"✓ Automatically connected {inviter.name} with {new_user.name}")
        
        return True
        
    except Exception as e:
        logging.error(f"Error connecting users automatically: {str(e)}")
        db.session.rollback()
        return False

def update_chat_streak(user_id):
    from models import ChatStreak
    user = User.query.get(user_id)
    if user.partner:
        streak = ChatStreak.query.filter_by(couple_id=user_id).first()
        today = datetime.utcnow().date()
        
        if not streak:
            streak = ChatStreak(couple_id=user_id, streak_count=1, last_chat_date=today)
            db.session.add(streak)
        else:
            if streak.last_chat_date == today - timedelta(days=1):
                streak.streak_count += 1
            elif streak.last_chat_date < today - timedelta(days=1):
                streak.streak_count = 1
            
            streak.last_chat_date = today
            streak.longest_streak = max(streak.longest_streak, streak.streak_count)
        
        db.session.commit()

if __name__ == '__main__':
    app = create_app()
    
    with app.app_context():
        db.create_all()
    
    print("\n" + "="*70)
    print("🚀 LunaLink Server Starting...")
    print("="*70)
    print("📧 Email Debug Routes Available:")
    print("   GET  /debug/email-status     - Comprehensive email system status")
    print("   POST /debug/send-test-otp    - Send test OTP email")
    print("   GET  /debug/email-config     - Show current email configuration")
    print("   GET  /debug/last-otp         - Get last generated OTP")
    print("   POST /debug/test-email-connection - Test email connectivity")
    print("   POST /debug/fix-email-config - Apply common email fixes")
    print("   POST /debug/clear-otps       - Clear all OTPs (testing)")
    print("="*70)
    print("💡 Tip: Visit /debug/email-status to check your email configuration")
    print("="*70 + "\n")
    
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)