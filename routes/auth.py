import random
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from extensions import db
from models import User

auth_bp = Blueprint('auth', __name__)

def is_password_strong(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character."
    return True, ""

def send_otp_email(to_email, otp_code):
    sender_email = (current_app.config.get('MAIL_USERNAME') or '').strip()
    sender_password = (current_app.config.get('MAIL_PASSWORD') or '').strip().replace(" ", "")

    # Always log clearly to console/terminal for developer convenience
    print(f"\n=======================================================")
    print(f"[DEV / CONSOLE] OTP for {to_email}: {otp_code}")
    print(f"=======================================================\n")

    if not sender_email or not sender_password or 'your-email' in sender_email:
        print("[SMTP] Mail credentials not set in .env. Falling back to console OTP.")
        return False

    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = "Gym Tracker - Email Verification Code"

        body = (
            f"Hello,\n\n"
            f"Your 6-digit email verification code is: {otp_code}\n\n"
            f"This code is required to activate your Gym Tracker account.\n"
            f"If you did not request this code, please ignore this email.\n"
        )
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP('smtp.gmail.com', 587, timeout=10)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, msg.as_string())
        server.quit()
        print(f"[SMTP SUCCESS] Verification email successfully sent to {to_email}")
        return True
    except Exception as e:
        print(f"[SMTP ERROR] Email sending failed: {e}")
        return False

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('user.dashboard'))
    
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        email = (request.form.get('email') or '').strip().lower()
        password = request.form.get('password')

        user_exists = User.query.filter((User.username == username) | (User.email == email)).first()
        if user_exists:
            # If account exists but was never verified, allow resending OTP instead of blocking
            if not user_exists.is_verified and user_exists.email == email:
                otp = f"{random.randint(100000, 999999)}"
                user_exists.otp_code = otp
                if password:
                    user_exists.set_password(password)
                db.session.commit()
                email_sent = send_otp_email(email, otp)
                if email_sent:
                    flash('A fresh verification code has been sent to your email.', 'info')
                else:
                    flash('Fresh code generated. Email delivery failed (check console/terminal for OTP).', 'warning')
                return redirect(url_for('auth.verify_otp', email=email))

            flash('Username or email already exists.', 'danger')
            return redirect(url_for('auth.signup'))

        # Check password strength
        is_valid, error_msg = is_password_strong(password)
        if not is_valid:
            flash(error_msg, 'danger')
            return redirect(url_for('auth.signup'))

        # Generate 6-digit OTP
        otp = f"{random.randint(100000, 999999)}"

        new_user = User(username=username, email=email, is_verified=False, otp_code=otp)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        # Send OTP email
        email_sent = send_otp_email(email, otp)
        if email_sent:
            flash('Account created! Please check your email for the 6-digit verification code.', 'info')
        else:
            flash('Account created! Email could not be delivered (check console/terminal for OTP or verify Gmail credentials in .env).', 'warning')

        return redirect(url_for('auth.verify_otp', email=email))
        
    return render_template('auth/signup.html')

@auth_bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    email = request.args.get('email') or request.form.get('email')
    
    if not email:
        flash('Please log in or sign up first.', 'warning')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        entered_otp = (request.form.get('otp') or '').strip()
        user = User.query.filter_by(email=email).first()

        if user and user.otp_code and user.otp_code == entered_otp:
            user.is_verified = True
            user.otp_code = None
            db.session.commit()
            flash('Email verified successfully! You can now log in.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Invalid verification code. Please try again.', 'danger')

    return render_template('auth/verify_otp.html', email=email)

@auth_bp.route('/resend-otp', methods=['GET', 'POST'])
def resend_otp():
    email = request.args.get('email') or request.form.get('email')
    if not email:
        flash('Email address required to resend verification code.', 'danger')
        return redirect(url_for('auth.login'))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash('No account found with this email.', 'danger')
        return redirect(url_for('auth.signup'))

    if user.is_verified:
        flash('Account is already verified. Please log in.', 'info')
        return redirect(url_for('auth.login'))

    otp = f"{random.randint(100000, 999999)}"
    user.otp_code = otp
    db.session.commit()

    email_sent = send_otp_email(email, otp)
    if email_sent:
        flash('A new verification code has been sent to your email.', 'info')
    else:
        flash('New code generated! Email delivery failed (check console/terminal for OTP).', 'warning')

    return redirect(url_for('auth.verify_otp', email=email))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('user.dashboard'))
        
    if request.method == 'POST':
        email = (request.form.get('email') or '').strip().lower()
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            if not user.is_verified:
                flash('Please verify your email address before logging in.', 'warning')
                return redirect(url_for('auth.verify_otp', email=email))

            login_user(user)
            flash('Logged in successfully!', 'success')
            if user.is_admin:
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('user.dashboard'))
        else:
            flash('Invalid email or password.', 'danger')
            
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))