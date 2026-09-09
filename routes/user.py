import csv
import io
from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect, url_for, flash, Response
from flask_login import login_required, current_user
from extensions import db
from models import Workout

user_bp = Blueprint('user', __name__)

@user_bp.route('/dashboard')
@login_required
def dashboard():
    user_workouts = Workout.query.filter_by(user_id=current_user.id).order_by(Workout.date.desc()).all()
    
    if current_user.created_at:
        # Support timezone-aware or naive datetimes cleanly
        created = current_user.created_at
        now = datetime.now(timezone.utc) if created.tzinfo else datetime.utcnow()
        delta = now - created
        days_remaining = max(0, 30 - delta.days)
    else:
        days_remaining = 30

    chart_data = [
        {
            "date": w.date.strftime('%b %d'),
            "volume": w.sets * w.reps * w.weight
        }
        for w in reversed(user_workouts)
    ]

    return render_template(
        'user/dashboard.html', 
        workouts=user_workouts, 
        days_remaining=days_remaining,
        chart_data=chart_data
    )

@user_bp.route('/workout/add', methods=['POST'])
@login_required
def add_workout():
    if not current_user.can_add_workout(limit=10):
        if not current_user.is_trial_active():
            flash('Your 30-day free trial has expired!', 'danger')
        else:
            flash('Trial workout limit reached (10/10 workouts used).', 'warning')
        return redirect(url_for('user.dashboard'))

    exercise_name = (request.form.get('exercise_name') or '').strip()
    sets = request.form.get('sets')
    reps = request.form.get('reps')
    weight = request.form.get('weight')
    notes = (request.form.get('notes') or '').strip()

    if not exercise_name or not sets or not reps or not weight:
        flash('Please fill in all required workout fields.', 'danger')
        return redirect(url_for('user.dashboard'))

    try:
        sets_val = int(sets)
        reps_val = int(reps)
        weight_val = float(weight)
        if sets_val <= 0 or reps_val <= 0 or weight_val < 0:
            raise ValueError()
    except ValueError:
        flash('Please enter valid positive numbers for sets, reps, and weight.', 'danger')
        return redirect(url_for('user.dashboard'))

    new_workout = Workout(
        exercise_name=exercise_name,
        sets=sets_val,
        reps=reps_val,
        weight=weight_val,
        notes=notes,
        user_id=current_user.id
    )
    db.session.add(new_workout)
    db.session.commit()
    flash('Workout logged successfully!', 'success')
    return redirect(url_for('user.dashboard'))

@user_bp.route('/workout/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_workout(id):
    workout = Workout.query.get_or_404(id)
    if workout.user_id != current_user.id:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('user.dashboard'))

    if request.method == 'POST':
        exercise_name = (request.form.get('exercise_name') or '').strip()
        sets = request.form.get('sets')
        reps = request.form.get('reps')
        weight = request.form.get('weight')
        notes = (request.form.get('notes') or '').strip()

        if not exercise_name or not sets or not reps or not weight:
            flash('Please fill in all required fields.', 'danger')
            return render_template('user/edit_workout.html', workout=workout)

        try:
            sets_val = int(sets)
            reps_val = int(reps)
            weight_val = float(weight)
            if sets_val <= 0 or reps_val <= 0 or weight_val < 0:
                raise ValueError()
        except ValueError:
            flash('Please enter valid positive numbers for sets, reps, and weight.', 'danger')
            return render_template('user/edit_workout.html', workout=workout)

        workout.exercise_name = exercise_name
        workout.sets = sets_val
        workout.reps = reps_val
        workout.weight = weight_val
        workout.notes = notes
        db.session.commit()

        flash('Workout updated successfully!', 'success')
        return redirect(url_for('user.dashboard'))

    return render_template('user/edit_workout.html', workout=workout)

@user_bp.route('/workout/delete/<int:id>', methods=['POST'])
@login_required
def delete_workout(id):
    workout = Workout.query.get_or_404(id)
    if workout.user_id != current_user.id:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('user.dashboard'))

    db.session.delete(workout)
    db.session.commit()
    flash('Workout entry removed.', 'info')
    return redirect(url_for('user.dashboard'))

@user_bp.route('/export/csv')
@login_required
def export_csv():
    workouts = Workout.query.filter_by(user_id=current_user.id).order_by(Workout.date.asc()).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Exercise Name', 'Sets', 'Reps', 'Weight (kg)', 'Total Volume (kg)', 'Notes'])
    
    for w in workouts:
        total_volume = w.sets * w.reps * w.weight
        writer.writerow([w.date.strftime('%Y-%m-%d %H:%M'), w.exercise_name, w.sets, w.reps, w.weight, total_volume, w.notes or ''])
        
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={"Content-Disposition": "attachment;filename=workout_logs.csv"}
    )