import logging
from flask import Blueprint, jsonify, session
from models import User, Email
from flask_login import login_required, current_user
from sqlalchemy import desc

logger = logging.getLogger(__name__)

bp = Blueprint('emails', __name__, url_prefix='/api')

@bp.route('/emails', methods=['GET'])
@login_required
def emails():
    logger.debug(f"Emails route - current_user: {current_user}, is_authenticated: {current_user.is_authenticated}")
    logger.debug(f"Session: {dict(session)}")
    
    user = User.query.filter_by(username=current_user.username).first()
    if not user:
        logger.error("User not found in database")
        return jsonify({"error": "User not found"}), 404
        
    logger.debug(f"Found user in DB: {user.id}, emails: {len(user.emails) if user.emails else 0}")
    sorted_emails = Email.query.filter_by(user_id=user.id).order_by(desc(Email.received_at)).all()
    return jsonify([email.to_dict() for email in sorted_emails])
