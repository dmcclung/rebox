from flask import Blueprint, jsonify, session
from db import db
from models import User

bp = Blueprint('emails', __name__)

@bp.route('/emails', methods=['GET'])
def emails():
    if 'username' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    user = User.query.filter_by(username=session['username']).first()
    return jsonify([email.to_dict() for email in user.emails])
