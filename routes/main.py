from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login_page'))
    return render_template("emails.html")

@bp.route('/aliases')
@login_required
def aliases():
    return render_template('aliases.html')