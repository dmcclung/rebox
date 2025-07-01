import logging
from flask import Blueprint, jsonify, request, current_app, session
from flask_login import login_required, current_user
from models.email_alias import EmailAlias
from db import db

logger = logging.getLogger(__name__)

bp = Blueprint('aliases', __name__, url_prefix='/api')

@bp.route('/aliases', methods=['GET'])
@login_required
def list_aliases():
    """List all email aliases for the current user"""
    logger.debug(f"Aliases route - current_user: {current_user}, is_authenticated: {current_user.is_authenticated}")
    logger.debug(f"Session: {dict(session)}")
    
    aliases = EmailAlias.query.filter_by(user_id=current_user.id).all()
    logger.debug(f"Found {len(aliases)} aliases for user {current_user.id}")
    return jsonify([alias.to_dict() for alias in aliases])

@bp.route('/aliases', methods=['POST'])
@login_required
def create_alias():
    """Create a new email alias"""
    data = request.get_json()
    
    # Generate a random prefix
    prefix = EmailAlias.generate_alias_prefix()
    
    # Create the alias
    alias = EmailAlias(
        alias_prefix=prefix,
        alias_domain=current_app.config.get('EMAIL_DOMAIN', 'rebox.sh'),
        description=data.get('description', ''),
        forwarding_email=data['forwarding_email'],
        user_id=current_user.id
    )
    
    db.session.add(alias)
    db.session.commit()
    
    return jsonify(alias.to_dict()), 201

@bp.route('/aliases/<int:alias_id>', methods=['DELETE'])
@login_required
def delete_alias(alias_id):
    """Delete an email alias"""
    alias = EmailAlias.query.filter_by(id=alias_id, user_id=current_user.id).first_or_404()
    
    db.session.delete(alias)
    db.session.commit()
    
    return '', 204

@bp.route('/aliases/<int:alias_id>', methods=['PUT'])
@login_required
def update_alias(alias_id):
    """Update an existing email alias"""
    alias = EmailAlias.query.filter_by(id=alias_id, user_id=current_user.id).first_or_404()
    data = request.get_json()
    
    if 'description' in data:
        alias.description = data['description']
    if 'forwarding_email' in data:
        alias.forwarding_email = data['forwarding_email']
    
    db.session.commit()
    
    return jsonify(alias.to_dict())
