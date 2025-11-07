from ast import main
from flask import Blueprint, current_app, logging, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Message
from datetime import datetime, timedelta
import random
import string

from models import db, User, OTP, UserSettings
from utils.email_sender import send_verification_email
from utils.encryption import generate_otp
from utils.helpers import validate_email

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    # Get invitation code from URL
    invite_code = request.args.get('invite')
    inviter = None
    if invite_code:
        inviter = User.query.get(invite_code)
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return render_template('auth/signup.html', inviter=inviter, invite_code=invite_code)
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered!', 'error')
            return render_template('auth/signup.html', inviter=inviter, invite_code=invite_code)
        
        # Create user
        new_user = User(
            name=name,
            email=email,
            is_verified=False
        )
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        # Create default settings
        settings = UserSettings(user_id=new_user.id)
        db.session.add(settings)
        db.session.commit()
        
        # If this was an invitation, store the invitation info
        if invite_code and inviter:
            new_user.invited_by_id = inviter.id
            new_user.invitation_sent_at = datetime.utcnow()
            db.session.commit()
        
        # Send OTP
        otp_code = generate_otp()
        send_verification_email(email, otp_code, new_user.name)
        
        # Store OTP in database
        otp = OTP(
            email=email,
            otp_code=otp_code,
            purpose='verification',
            expires_at=datetime.utcnow() + timedelta(minutes=5)
        )
        db.session.add(otp)
        db.session.commit()
        
        flash('Verification email sent! Please check your inbox.', 'success')
        return redirect(url_for('auth.verify_otp', email=email))
    
    return render_template('auth/signup.html', inviter=inviter, invite_code=invite_code)

@auth_bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    email = request.args.get('email')
    
    if not email:
        return redirect(url_for('auth.signup'))
    
    if request.method == 'POST':
        otp_code = request.form.get('otp')
        
        # Find valid OTP
        otp = OTP.query.filter_by(
            email=email, 
            otp_code=otp_code, 
            purpose='verification',
            is_used=False
        ).first()
        
        if not otp or otp.is_expired():
            flash('Invalid or expired OTP!', 'error')
            return render_template('auth/verify_otp.html', email=email)
        
        # Mark OTP as used and verify user
        otp.is_used = True
        user = User.query.filter_by(email=email).first()
        user.is_verified = True
        
        # If user was invited, automatically connect with inviter
        if user.invited_by_id:
            from app import connect_users_automatically
            success = connect_users_automatically(user.invited_by_id, user)
            
            if success:
                # Send connection emails
                send_connection_emails(user.invited_by_id, user.id)
                flash(f'🎉 You are now connected with {User.query.get(user.invited_by_id).name}! You can start chatting immediately!', 'success')
            else:
                flash('Connected with your partner! You can now start chatting.', 'success')
        
        db.session.commit()
        
        flash('Email verified successfully! You can now login.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/verify_otp.html', email=email)

def send_connection_emails(inviter_id, new_user_id):
    """Send emails to both users when they're connected"""
    try:
        inviter = User.query.get(inviter_id)
        new_user = User.query.get(new_user_id)
        
        if not inviter or not new_user:
            return
        
        # Send email to inviter
        inviter_msg = Message(
            subject=f"🎉 {new_user.name} Accepted Your Invitation!",
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[inviter.email]
        )
        
        inviter_msg.html = f"""
        <h1>Great News! 🎉</h1>
        <p><strong>{new_user.name}</strong> has accepted your invitation and joined LunaLink!</p>
        <p>You're now automatically connected and can start chatting immediately.</p>
        <p>
            <a href="{url_for('chat.chat_room', _external=True)}" 
               style="background: #4a90e2; color: white; padding: 12px 24px; 
               text-decoration: none; border-radius: 6px; display: inline-block; font-weight: bold;">
                Start Chatting Now
            </a>
        </p>
        <p>Your love journey together begins now! 💕</p>
        """
        
        # Send email to new user
        new_user_msg = Message(
            subject=f"🎉 You're Connected with {inviter.name}!",
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[new_user.email]
        )
        
        new_user_msg.html = f"""
        <h1>Welcome to LunaLink! 🌙</h1>
        <p>You're now connected with <strong>{inviter.name}</strong>!</p>
        <p>Your private chat is ready and waiting for you.</p>
        <p>
            <a href="{url_for('chat.chat_room', _external=True)}" 
               style="background: #4a90e2; color: white; padding: 12px 24px; 
               text-decoration: none; border-radius: 6px; display: inline-block; font-weight: bold;">
                Start Your First Conversation
            </a>
        </p>
        <p>We've sent your first message to get you started. Enjoy your journey together! 💕</p>
        """
        
        mail.send(inviter_msg)
        mail.send(new_user_msg)
        
        logging.info(f"Sent connection emails to {inviter.name} and {new_user.name}")
        
    except Exception as e:
        logging.error(f"Error sending connection emails: {str(e)}")

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember_me = bool(request.form.get('remember_me'))
        
        user = User.query.filter_by(email=email).first()
        
        if not user:
            flash('Invalid email or password!', 'error')
            return render_template('auth/login.html')
        
        if user.is_locked():
            flash('Account locked due to too many failed attempts!', 'error')
            return render_template('auth/login.html')
        
        if not user.check_password(password):
            user.login_attempts += 1
            db.session.commit()
            flash('Invalid email or password!', 'error')
            return render_template('auth/login.html')
        
        if not user.is_verified:
            flash('Please verify your email first!', 'error')
            return render_template('auth/login.html')
        
        # Successful login
        user.reset_login_attempts()
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        login_user(user, remember=remember_me)
        flash(f'Welcome back, {user.name}! 💞', 'success')
        
        next_page = request.args.get('next')
        return redirect(next_page or url_for('index'))
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully!', 'success')
    return redirect(url_for('index'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user:
            otp_code = generate_otp()
            send_verification_email(email, otp_code, user.name, purpose='reset')
            
            otp = OTP(
                email=email,
                otp_code=otp_code,
                purpose='reset',
                expires_at=datetime.utcnow() + timedelta(minutes=5)
            )
            db.session.add(otp)
            db.session.commit()
        
        flash('If the email exists, a password reset link has been sent!', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html')

@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    email = request.args.get('email')
    otp_code = request.args.get('otp')
    
    if not email or not otp_code:
        flash('Invalid reset link!', 'error')
        return redirect(url_for('auth.login'))
    
    otp = OTP.query.filter_by(
        email=email, 
        otp_code=otp_code, 
        purpose='reset',
        is_used=False
    ).first()
    
    if not otp or otp.is_expired():
        flash('Invalid or expired reset link!', 'error')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return render_template('auth/reset_password.html', email=email, otp=otp_code)
        
        user = User.query.filter_by(email=email).first()
        user.set_password(password)
        otp.is_used = True
        
        db.session.commit()
        
        flash('Password reset successfully! You can now login.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', email=email, otp=otp_code)

@auth_bp.route('/invite-partner', methods=['POST'])
@login_required
def invite_partner():
    email = request.json.get('email')
    
    if not email or not validate_email(email):
        return jsonify({'success': False, 'error': 'Invalid email address'})
    
    # Check if user exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({'success': False, 'error': 'User with this email already exists'})
    
    try:
        # Send invitation email
        from utils.email_sender import send_invitation_email
        send_invitation_email(email, current_user.name, current_user.email)
        
        return jsonify({
            'success': True, 
            'message': f'Invitation sent to {email}'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': 'Failed to send invitation'})