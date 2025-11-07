from flask_mail import Message
from flask import render_template, url_for, current_app
from threading import Thread
from flask_mail import Mail
import logging
import os
import time
from datetime import datetime

# Set up logging
logger = logging.getLogger(__name__)

# Create mail instance
mail = Mail()

def send_async_email(app, msg):
    """
    Send email asynchronously to avoid blocking the main thread
    """
    with app.app_context():
        try:
            print(f"📧 Attempting to send email to: {msg.recipients}")
            print(f"📧 Using MAIL_SERVER: {app.config.get('MAIL_SERVER')}")
            print(f"📧 Using MAIL_PORT: {app.config.get('MAIL_PORT')}")
            print(f"📧 Using MAIL_USERNAME: {app.config.get('MAIL_USERNAME')}")
            print(f"📧 Using MAIL_USE_TLS: {app.config.get('MAIL_USE_TLS')}")
            print(f"📧 Using MAIL_DEFAULT_SENDER: {app.config.get('MAIL_DEFAULT_SENDER')}")
            
            start_time = time.time()
            mail.send(msg)
            end_time = time.time()
            
            logger.info(f"Email sent successfully to: {msg.recipients}")
            print(f"✅ Email sent successfully to: {msg.recipients}")
            print(f"⏱️  Email sent in {end_time - start_time:.2f} seconds")
            return True
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            print(f"❌ Error sending email: {str(e)}")
            import traceback
            traceback_str = traceback.format_exc()
            logger.error(f"Full traceback: {traceback_str}")
            print(f"Full traceback: {traceback_str}")
            
            # Provide specific guidance for common errors
            error_msg = str(e).lower()
            if "authentication failed" in error_msg:
                print("🔐 AUTHENTICATION ERROR: Check your email password/App Password")
                print("   For Gmail, make sure:")
                print("   1. 2-Factor Authentication is enabled")
                print("   2. You're using an App Password, not your regular password")
                print("   3. Go to: Google Account → Security → 2-Step Verification → App passwords")
            elif "connection refused" in error_msg:
                print("🌐 CONNECTION ERROR: Check your MAIL_SERVER and MAIL_PORT")
                print("   Common settings:")
                print("   - Gmail: smtp.gmail.com:587")
                print("   - Outlook: smtp-mail.outlook.com:587")
                print("   - Yahoo: smtp.mail.yahoo.com:587")
            elif "ssl" in error_msg:
                print("🔒 SSL ERROR: Try changing MAIL_USE_TLS to True or MAIL_USE_SSL to False")
            elif "smtplib" in error_msg:
                print("📧 SMTP LIBRARY ERROR: Check your SMTP server configuration")
            elif "timed out" in error_msg:
                print("⏰ TIMEOUT ERROR: SMTP server is not responding. Check firewall/network settings")
            
            return False

def send_email(subject, recipients, html_body, text_body=None, app=None):
    """
    Send email with HTML and optional plain text version
    """
    if app is None:
        app = current_app._get_current_object()
    
    # Debug: Print email configuration
    print(f"\n🔧 Email Configuration Check:")
    print(f"   MAIL_SERVER: {app.config.get('MAIL_SERVER')}")
    print(f"   MAIL_PORT: {app.config.get('MAIL_PORT')}")
    print(f"   MAIL_USERNAME: {app.config.get('MAIL_USERNAME')}")
    print(f"   MAIL_USE_TLS: {app.config.get('MAIL_USE_TLS')}")
    print(f"   MAIL_DEFAULT_SENDER: {app.config.get('MAIL_DEFAULT_SENDER')}")
    print(f"   DEBUG: {app.config.get('DEBUG')}")
    print(f"   PRINT_EMAILS_TO_CONSOLE: {app.config.get('PRINT_EMAILS_TO_CONSOLE')}")
    
    # Check if we're in development mode and should print to console instead
    if app.config.get('DEBUG') and app.config.get('PRINT_EMAILS_TO_CONSOLE', True):
        print("\n" + "="*80)
        print("📧 EMAIL WOULD BE SENT (Development Mode - Printed to console):")
        print("="*80)
        print(f"To: {recipients}")
        print(f"Subject: {subject}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        if text_body:
            print(f"Text Body:\n{text_body}")
        print(f"HTML Body Preview:\n{html_body[:500]}...")
        print("="*80 + "\n")
        return True
    
    # Create message
    msg = Message(
        subject=subject,
        recipients=recipients,
        html=html_body,
        sender=app.config.get('MAIL_DEFAULT_SENDER', 'noreply@lunalink.com')
    )
    
    # Add plain text alternative if provided
    if text_body:
        msg.body = text_body
    
    # Send email asynchronously
    try:
        print(f"🚀 Starting email thread for: {recipients}")
        print(f"📝 Subject: {subject}")
        thread = Thread(target=send_async_email, args=(app, msg))
        thread.daemon = True
        thread.start()
        print(f"✅ Email thread started successfully at {datetime.now().strftime('%H:%M:%S')}")
        return True
    except Exception as e:
        logger.error(f"Error starting email thread: {str(e)}")
        print(f"❌ Error starting email thread: {str(e)}")
        import traceback
        print(f"Thread traceback: {traceback.format_exc()}")
        return False

def send_verification_email(email, otp_code, name, purpose='verification'):
    """
    Send verification email for account verification or password reset
    """
    try:
        print(f"\n🎯 Preparing {purpose} email for: {email}")
        print(f"🔢 OTP Code: {otp_code}")
        print(f"👤 User Name: {name}")
        
        # If in debug mode, just print and return success
        if current_app.config.get('DEBUG') and current_app.config.get('PRINT_EMAILS_TO_CONSOLE', True):
            print(f"\n{'='*60}")
            print(f"📧 OTP EMAIL FOR {email}:")
            print(f"🔢 OTP CODE: {otp_code}")
            print(f"🎯 PURPOSE: {purpose}")
            print(f"👤 USER: {name}")
            print(f"⏰ TIMESTAMP: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*60}\n")
            
            # Store OTP in a temporary file for easy access during development
            try:
                with open('last_otp.txt', 'w') as f:
                    f.write(f"Email: {email}\n")
                    f.write(f"OTP: {otp_code}\n")
                    f.write(f"Purpose: {purpose}\n")
                    f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                print(f"💾 OTP saved to 'last_otp.txt' for easy reference")
            except Exception as file_error:
                print(f"⚠️  Could not save OTP to file: {file_error}")
            
            return True
        
        if purpose == 'verification':
            subject = "LunaLink - Verify Your Love Link 💞"
            template = 'emails/verification.html'
            verify_url = url_for('auth.verify_otp', email=email, _external=True)
        else:
            subject = "LunaLink - Password Reset 💌"
            template = 'emails/password_reset.html'
            verify_url = url_for('auth.reset_password', email=email, otp=otp_code, _external=True)
        
        print(f"📝 Using template: {template}")
        print(f"🔗 Generated URL: {verify_url}")
        
        # Render HTML template
        html_body = render_template(
            template,
            name=name,
            otp=otp_code,
            verify_url=verify_url,
            purpose=purpose
        )
        
        # Create plain text version
        text_body = f"""
Hello {name},

{'Your verification code for LunaLink is: ' + otp_code if purpose == 'verification' else 'Your password reset code for LunaLink is: ' + otp_code}

Please use this code to complete your {'verification' if purpose == 'verification' else 'password reset'} process.

Reset Link: {verify_url}
Code: {otp_code}

This code will expire in 10 minutes.

If you didn't request this, please ignore this email.

With love,
The LunaLink Team 💕
        """
        
        # Send email
        success = send_email(subject, [email], html_body, text_body)
        
        if success:
            logger.info(f"Verification email sent to {email} for {purpose}")
            print(f"✅ Verification email sent to {email} for {purpose}")
        else:
            logger.error(f"Failed to send verification email to {email}")
            print(f"❌ Failed to send verification email to {email}")
            
        return success
        
    except Exception as e:
        logger.error(f"Error in send_verification_email: {str(e)}")
        print(f"❌ Error in send_verification_email: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return False

def send_invitation_email(to_email, inviter_name, inviter_email, invitation_token=None):
    """
    Send invitation email to join LunaLink
    """
    try:
        print(f"\n💌 Preparing invitation email to: {to_email}")
        print(f"👤 From: {inviter_name} ({inviter_email})")
        
        # If in debug mode, just print and return success
        if current_app.config.get('DEBUG') and current_app.config.get('PRINT_EMAILS_TO_CONSOLE', True):
            print(f"\n{'='*60}")
            print(f"📧 INVITATION EMAIL FOR {to_email}:")
            print(f"👤 FROM: {inviter_name} ({inviter_email})")
            print(f"⏰ TIMESTAMP: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            if invitation_token:
                print(f"🔗 INVITATION TOKEN: {invitation_token}")
            print(f"{'='*60}\n")
            return True
        
        subject = f"Join LunaLink - {inviter_name} Invited You! 💞"
        
        # Generate signup URL with invitation token if provided
        if invitation_token:
            signup_url = url_for('auth.signup', token=invitation_token, _external=True)
        else:
            signup_url = url_for('auth.signup', _external=True)
        
        # Render HTML template
        html_body = render_template(
            'emails/invitation.html',
            inviter_name=inviter_name,
            inviter_email=inviter_email,
            signup_url=signup_url
        )
        
        # Create plain text version
        text_body = f"""
💌 You're Invited to Join LunaLink!

Hello there!

{inviter_name} ({inviter_email}) has invited you to join LunaLink, 
the private couple messaging app designed to strengthen your connection.

With LunaLink, you can:
• 💌 Send private messages to your partner
• 📸 Share photos and media securely
• 🎵 Share background music and moods
• ❤️ Strengthen your relationship through dedicated communication

Click here to accept the invitation and join:
{signup_url}

If you have any questions, feel free to reply to this email.

With love,
The LunaLink Team 💕

This invitation was sent by {inviter_name}. 
If you believe you received this in error, please ignore this email.
        """
        
        # Send email
        success = send_email(subject, [to_email], html_body, text_body)
        
        if success:
            logger.info(f"Invitation email sent to {to_email} from {inviter_name}")
            print(f"✅ Invitation email sent to {to_email} from {inviter_name}")
        else:
            logger.error(f"Failed to send invitation email to {to_email}")
            print(f"❌ Failed to send invitation email to {to_email}")
            
        return success
        
    except Exception as e:
        logger.error(f"Error in send_invitation_email: {str(e)}")
        print(f"❌ Error in send_invitation_email: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return False

def send_welcome_email(email, name):
    """
    Send welcome email after successful registration
    """
    try:
        print(f"\n🎉 Preparing welcome email for: {email}")
        print(f"👤 User: {name}")
        
        # If in debug mode, just print and return success
        if current_app.config.get('DEBUG') and current_app.config.get('PRINT_EMAILS_TO_CONSOLE', True):
            print(f"\n{'='*60}")
            print(f"📧 WELCOME EMAIL FOR {email}:")
            print(f"👤 USER: {name}")
            print(f"⏰ TIMESTAMP: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*60}\n")
            return True
        
        subject = "Welcome to LunaLink - Your Love Journey Begins! 🌙"
        
        dashboard_url = url_for('chat.chat_room', _external=True)
        
        html_body = render_template(
            'emails/welcome.html',
            name=name,
            dashboard_url=dashboard_url
        )
        
        text_body = f"""
Welcome to LunaLink, {name}! 🌙💫

We're thrilled to have you join our community of couples strengthening their connections.

Your love journey begins now! Here's what you can do:
• Connect with your partner
• Start private conversations
• Share special moments
• Build your love timeline

Get started: {dashboard_url}

If you need any help, don't hesitate to contact us.

With love and sparkles,
The LunaLink Team 💕
        """
        
        success = send_email(subject, [email], html_body, text_body)
        
        if success:
            logger.info(f"Welcome email sent to {email}")
            print(f"✅ Welcome email sent to {email}")
        else:
            logger.error(f"Failed to send welcome email to {email}")
            print(f"❌ Failed to send welcome email to {email}")
            
        return success
        
    except Exception as e:
        logger.error(f"Error in send_welcome_email: {str(e)}")
        print(f"❌ Error in send_welcome_email: {str(e)}")
        return False

def send_partner_connected_email(user_email, user_name, partner_name):
    """
    Send email notification when partners connect
    """
    try:
        print(f"\n🤝 Preparing partner connection email for: {user_email}")
        print(f"👤 User: {user_name}")
        print(f"💑 Partner: {partner_name}")
        
        # If in debug mode, just print and return success
        if current_app.config.get('DEBUG') and current_app.config.get('PRINT_EMAILS_TO_CONSOLE', True):
            print(f"\n{'='*60}")
            print(f"📧 PARTNER CONNECTED EMAIL FOR {user_email}:")
            print(f"👤 USER: {user_name}")
            print(f"💑 PARTNER: {partner_name}")
            print(f"⏰ TIMESTAMP: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*60}\n")
            return True
        
        subject = f"🎉 You're Now Connected with {partner_name} on LunaLink!"
        
        chat_url = url_for('chat.chat_room', _external=True)
        
        html_body = render_template(
            'emails/partner_connected.html',
            user_name=user_name,
            partner_name=partner_name,
            chat_url=chat_url
        )
        
        text_body = f"""
Celebration Time! 🎉

Dear {user_name},

Great news! You're now connected with {partner_name} on LunaLink!

Your private love space is ready. Start your journey together:
{chat_url}

Share your first message, upload a special photo, or simply say hello!

May your connection grow stronger every day.

With love,
The LunaLink Team 💕
        """
        
        success = send_email(subject, [user_email], html_body, text_body)
        
        if success:
            logger.info(f"Partner connected email sent to {user_email}")
            print(f"✅ Partner connected email sent to {user_email}")
        else:
            logger.error(f"Failed to send partner connected email to {user_email}")
            print(f"❌ Failed to send partner connected email to {user_email}")
            
        return success
        
    except Exception as e:
        logger.error(f"Error in send_partner_connected_email: {str(e)}")
        print(f"❌ Error in send_partner_connected_email: {str(e)}")
        return False

# Utility function to check email configuration
def check_email_config():
    """
    Check if email configuration is properly set up
    """
    required_configs = ['MAIL_SERVER', 'MAIL_PORT', 'MAIL_USERNAME', 'MAIL_PASSWORD']
    
    missing_configs = []
    for config in required_configs:
        if not current_app.config.get(config):
            missing_configs.append(config)
    
    if missing_configs:
        logger.warning(f"Missing email configurations: {', '.join(missing_configs)}")
        print(f"⚠️ Missing email configurations: {', '.join(missing_configs)}")
        return False
    
    # Check if we're using Gmail and remind about app passwords
    if 'gmail.com' in str(current_app.config.get('MAIL_USERNAME', '')):
        print("ℹ️  Remember: For Gmail, you need to use an App Password, not your regular password!")
        print("   Go to: Google Account → Security → 2-Step Verification → App passwords")
    
    logger.info("Email configuration check passed")
    print("✅ Email configuration check passed")
    return True

def test_email_configuration():
    """
    Test email configuration and send a test email
    """
    from flask import current_app
    
    print("\n🔧 Testing Email Configuration...")
    
    # Check required configurations
    required_configs = ['MAIL_SERVER', 'MAIL_PORT', 'MAIL_USERNAME', 'MAIL_PASSWORD', 'MAIL_DEFAULT_SENDER']
    missing_configs = []
    
    for config in required_configs:
        value = current_app.config.get(config)
        if not value:
            missing_configs.append(config)
        else:
            print(f"✅ {config}: {value if config != 'MAIL_PASSWORD' else '***'}")
    
    if missing_configs:
        print(f"❌ Missing configurations: {', '.join(missing_configs)}")
        return False
    
    print("✅ All required configurations present")
    
    # Test email sending
    try:
        test_subject = "LunaLink - Email Test"
        test_recipient = current_app.config['MAIL_USERNAME']  # Send to yourself
        test_html = """
        <h1>Email Test Successful! 🎉</h1>
        <p>If you're reading this, your email configuration is working correctly.</p>
        <p>LunaLink is ready to send emails!</p>
        """
        
        success = send_email(test_subject, [test_recipient], test_html)
        
        if success:
            print("✅ Test email sent successfully!")
            return True
        else:
            print("❌ Failed to send test email")
            return False
            
    except Exception as e:
        print(f"❌ Error during email test: {str(e)}")
        return False

def debug_email_system():
    """
    Comprehensive debug function for the email system
    """
    print("\n" + "="*70)
    print("🔍 EMAIL SYSTEM DEBUG")
    print("="*70)
    
    # Check configuration
    config_ok = check_email_config()
    
    if not config_ok:
        print("❌ Configuration check failed")
        return False
    
    # Test email sending
    print("\n📧 Testing email sending...")
    test_ok = test_email_configuration()
    
    if test_ok:
        print("✅ Email system is working correctly!")
    else:
        print("❌ Email system has issues")
        
    print("="*70)
    return test_ok

def get_last_otp():
    """
    Read the last OTP from file (for development debugging)
    """
    try:
        if os.path.exists('last_otp.txt'):
            with open('last_otp.txt', 'r') as f:
                return f.read()
        return "No OTP file found"
    except Exception as e:
        return f"Error reading OTP file: {str(e)}"

def print_email_status():
    """
    Print current email system status
    """
    print(f"\n📧 Email System Status:")
    print(f"   Debug Mode: {current_app.config.get('DEBUG', 'Unknown')}")
    print(f"   Print to Console: {current_app.config.get('PRINT_EMAILS_TO_CONSOLE', 'Unknown')}")
    print(f"   Mail Server: {current_app.config.get('MAIL_SERVER')}")
    print(f"   Mail Username: {current_app.config.get('MAIL_USERNAME')}")
    
    # Check last OTP
    last_otp = get_last_otp()
    print(f"   Last OTP: {last_otp.split(chr(10))[0] if chr(10) in last_otp else last_otp}")