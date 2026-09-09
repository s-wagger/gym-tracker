from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db

subscription_bp = Blueprint('subscription', __name__)

@subscription_bp.route('/checkout')
@login_required
def checkout():
    return render_template('subscription/checkout.html')

@subscription_bp.route('/upgrade', methods=['POST'])
@login_required
def upgrade():
    current_user.subscription_tier = 'pro'
    current_user.subscription_status = 'active'
    db.session.commit()
    flash('Congratulations! You have upgraded to Pro Tier with unlimited workout logs.', 'success')
    return redirect(url_for('user.dashboard'))