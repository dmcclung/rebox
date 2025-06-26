from flask import Blueprint, render_template, session

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    if 'username' in session:
        return render_template("emails.html")
    return render_template("login.html")