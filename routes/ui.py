from flask import Blueprint, render_template, redirect, url_for, send_from_directory, current_app, flash
from flask_login import login_required, current_user, logout_user
import os
from models import Email

bp = Blueprint('ui', __name__)

@bp.route('/')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('ui.login_page'))
    return render_template("emails.html")

@bp.route('/aliases')
@login_required
def aliases():
    return render_template('aliases.html')

@bp.route('/login', methods=['GET'])
def login_page():
    if current_user.is_authenticated:
        return redirect(url_for('ui.index'))
    return render_template('login.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('ui.login_page'))

@bp.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(current_app.root_path, 'static', 'images'),
                             'favicon.ico', mimetype='image/vnd.microsoft.icon')

@bp.route('/email/<int:email_id>')
@login_required
def view_email(email_id):
    email = Email.query.get(email_id)
    if not email or email.user_id != current_user.id:
        flash('Email not found or you do not have permission to view it.', 'danger')
        return redirect(url_for('ui.index'))
    return render_template('view_email.html', email=email)
