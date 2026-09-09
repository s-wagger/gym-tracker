from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from extensions import db, login_manager

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    # Verification & Security
    is_verified = db.Column(db.Boolean, default=False)
    otp_code = db.Column(db.String(6), nullable=True)

    # Account Lifecycle
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    subscription_tier = db.Column(db.String(20), default='free')    # 'free' or 'pro'
    subscription_status = db.Column(db.String(20), default='active')  # 'active' or 'canceled'

    workouts = db.relationship('Workout', backref='user', lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_trial_active(self):
        """Checks if the 30-day free trial is still valid."""
        if self.subscription_tier == 'pro' or self.is_admin:
            return True
        expiry_date = self.created_at + timedelta(days=30)
        return datetime.utcnow() <= expiry_date

    def can_add_workout(self, limit=10):
        """Capped at limit during trial, blocked if trial expired."""
        if not self.is_trial_active():
            return False
        if self.subscription_tier == 'pro' or self.is_admin:
            return True
        return len(self.workouts) < limit

    def __repr__(self):
        return f'<User {self.username}>'


class Workout(db.Model):
    __tablename__ = 'workouts'

    id = db.Column(db.Integer, primary_key=True)
    exercise_name = db.Column(db.String(100), nullable=False)
    sets = db.Column(db.Integer, nullable=False)
    reps = db.Column(db.Integer, nullable=False)
    weight = db.Column(db.Float, nullable=False)
    notes = db.Column(db.String(200), nullable=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def __repr__(self):
        return f'<Workout {self.exercise_name} - {self.weight}kg>'