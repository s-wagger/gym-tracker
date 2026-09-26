import re
from flask import Blueprint, flash, redirect, render_template, request, url_for
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
            flash('Username or email already exists. Please log in instead.', 'danger')
            return redirect(url_for('auth.signup'))

        is_valid, error_msg = is_password_strong(password)
        if not is_valid:
            flash(error_msg, 'danger')
            return redirect(url_for('auth.signup'))

        # No email verification step anymore — account is active immediately,
        # so anyone (not just the developer's own inbox) can sign up and use it.
        new_user = User(username=username, email=email, is_verified=True)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        # Log the new user straight in — no extra step after signing up.
        login_user(new_user)
        flash(f'Welcome, {new_user.username}! Your account is ready.', 'success')
        return redirect(url_for('user.dashboard'))

    return render_template('auth/signup.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('user.dashboard'))

    if request.method == 'POST':
        email = (request.form.get('email') or '').strip().lower()
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
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
