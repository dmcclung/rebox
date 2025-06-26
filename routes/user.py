from flask import Blueprint, session, redirect, url_for

bp = Blueprint('user', __name__)

@bp.route('/logout', methods=['GET'])
def logout():
    session.pop("username", None)
    return redirect(url_for('main.index'))
