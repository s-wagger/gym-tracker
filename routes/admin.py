from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models import User, Workout

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin/dashboard')
@login_required
def dashboard():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('user.dashboard'))

    users = User.query.all()
    total_workouts = Workout.query.count()
    return render_template('admin/admin_dashboard.html', users=users, total_workouts=total_workouts)

@admin_bp.route('/admin/toggle-subscription/<int:user_id>', methods=['POST'])
@login_required
def toggle_subscription(user_id):
    if not current_user.is_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('user.dashboard'))

    user = User.query.get_or_404(user_id)
    user.subscription_tier = 'free' if user.subscription_tier == 'pro' else 'pro'
    db.session.commit()
    
    flash(f"Updated {user.username}'s subscription tier to {user.subscription_tier.upper()}.", 'success')
    return redirect(url_for('admin.dashboard'))