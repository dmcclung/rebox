import logging
from flask import Blueprint, jsonify, request, current_app, session
from flask_login import login_required, current_user
from models.email_alias import EmailAlias
from models.user import User
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
    
    # Validate title (alphanumeric, no spaces or punctuation)
    title = data.get('title', '').strip().lower()
    if not title or not title.isalnum():
        return jsonify({'error': 'Title must be one alphanumeric word (no spaces or punctuation)'}), 400
    
    # Get or generate random component
    random_alias = data.get('random_alias')
    if not random_alias:
        random_alias = EmailAlias.generate_alias(title=title)

    # Final validation to prevent race conditions or conflicts
    full_prefix = f"{title}.{random_alias}"
    alias_domain = current_app.config.get('EMAIL_DOMAIN', 'rebox.sh')
    
    alias_exists = EmailAlias.query.filter_by(
        alias_title=title, 
        alias_random=random_alias,
        alias_domain=alias_domain
    ).first()
    
    user_exists = User.query.filter(User.username == full_prefix).first()

    if alias_exists or user_exists:
        return jsonify({'error': 'This alias is already taken. Please refresh to get a new one.'}), 409
    
    # Create the alias
    alias = EmailAlias(
        alias_title=title,
        alias_random=random_alias,
        alias_domain=alias_domain,
        description=data.get('description', ''),
        forwarding_email=data.get('forwarding_email'),
        user_id=current_user.id
    )
    
    db.session.add(alias)
    db.session.commit()
    
    return jsonify(alias.to_dict()), 201

@bp.route('/aliases/generate', methods=['GET'])
@login_required
def generate_alias():
    """Generate a random alias to be combined with a title"""
    title = request.args.get('title', '')
    return EmailAlias.generate_alias(title=title)

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
    
    # Validate title if being updated
    if 'alias_title' in data:
        title = data['alias_title'].strip().lower()
        if not title or not title.isalnum():
            return jsonify({'error': 'Title must be one alphanumeric word (no spaces or punctuation)'}), 400
        alias.alias_title = title
    
    # Update random component if provided
    if 'alias_random' in data and data['alias_random']:
        alias.alias_random = data['alias_random']
    
    # Update other fields if provided
    if 'description' in data:
        alias.description = data['description']
    if 'forwarding_email' in data:
        alias.forwarding_email = data['forwarding_email']
    
    db.session.commit()
    
    return jsonify(alias.to_dict())
