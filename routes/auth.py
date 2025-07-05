import logging
from flask import Blueprint, jsonify, session, request, current_app, url_for
from flask_login import login_user, current_user, login_required
import webauthn as webauthn

logger = logging.getLogger(__name__)
from webauthn.helpers.structs import (
    AttestationConveyancePreference, 
    AuthenticatorAttachment, 
    AuthenticatorSelectionCriteria,
    UserVerificationRequirement,
    PublicKeyCredentialDescriptor
)
import json
from db import db
from models.user import User
from base64 import urlsafe_b64encode

bp = Blueprint('auth', __name__, url_prefix='/api')

@bp.route('/generate-authentication-options', methods=['POST'])
def generate_authentication_options():
    username = request.json["username"]
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    try:
        credential_id = webauthn.base64url_to_bytes(user.credential_id)
        authentication_options = webauthn.generate_authentication_options(
            rp_id=current_app.config.get("RP_ID"),
            allow_credentials=[PublicKeyCredentialDescriptor(id=credential_id)],
            user_verification=UserVerificationRequirement.PREFERRED,
        )

        session['authentication_challenge'] = authentication_options.challenge
        session['authentication_username'] = username
        return jsonify(json.loads(webauthn.options_to_json(authentication_options)))
    except Exception as e:
        current_app.logger.error(f'Authentication options generation failed: {str(e)}')
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.route('/verify-authentication', methods=['POST'])
def verify_authentication():
    username = session.get('authentication_username')
    if not username:
        return jsonify({"error": "No authentication in progress"}), 400
        
    try:
        user = User.query.filter_by(username=username).first()
        if not user:
            logger.error(f"User not found: {username}")
            return jsonify({"error": "User not found"}), 404
            
        public_key = webauthn.base64url_to_bytes(user.public_key)
        webauthn.verify_authentication_response(
            credential=request.json,
            expected_challenge=session.get('authentication_challenge'),
            expected_rp_id=current_app.config.get("RP_ID"),
            expected_origin=current_app.config.get("EXPECTED_ORIGIN"),
            credential_public_key=public_key,
            credential_current_sign_count=0,
            require_user_verification=True,
        )
        
        # Debug logs before login
        # TODO: If a user is not active, they should not be able to login
        # We need to handle this and redirect to an error page
        logger.debug(f"Before login - user_id: {user.id}, is_active: {user.is_active}")
        
        # Log the user in with Flask-Login
        remember_me = request.json.get('remember_me', False)
        login_result = login_user(user, remember=remember_me)
        
        # Debug logs after login
        logger.debug(f"Login result: {login_result}")
        logger.debug(f"After login - user_id: {user.id}, is_authenticated: {user.is_authenticated}")
        logger.debug(f"Login user called with remember_me: {remember_me}")
        
        # Get the next URL if it exists
        next_url = request.args.get('next') or url_for('ui.index')
        
        # Clear the session
        session.pop('authentication_challenge', None)
        session.pop('authentication_username', None)
        
        return jsonify({"status": "success", "redirect": next_url})
        
    except Exception as e:
        current_app.logger.error(f'Authentication verification failed: {str(e)}')
        return jsonify({"status": "error", "message": str(e)}), 400

@bp.route('/generate-registration-options', methods=['POST'])
def generate_registration_options():
    username = request.json["username"]
    if not username:
        return jsonify({"status": "error", "message": "Username is required"}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({"status": "error", "message": "Username already exists"}), 400
    
    try:
        registration_options = webauthn.generate_registration_options(
            rp_id=current_app.config.get("RP_ID"),
            rp_name=current_app.config.get("RP_NAME"),
            user_id=username.encode("utf-8"),
            user_name=username,
            attestation=AttestationConveyancePreference.INDIRECT,
            authenticator_selection=AuthenticatorSelectionCriteria(
                authenticator_attachment=AuthenticatorAttachment.CROSS_PLATFORM,
                require_resident_key=True,
                user_verification=UserVerificationRequirement.PREFERRED
            )
        )
    except Exception as e:
        current_app.logger.error(f'Registration options generation failed: {str(e)}')
        return jsonify({"status": "error", "message": str(e)}), 500

    session['registration_challenge'] = registration_options.challenge
    session['registration_username'] = username

    return jsonify(json.loads(webauthn.options_to_json(registration_options)))

@bp.route('/verify-registration', methods=['POST'])
def verify_registration():
    username = session.get('registration_username')
    if not username:
        return jsonify({"error": "No registration in progress"}), 404
    try:
        registration_response = webauthn.verify_registration_response(
            credential=request.json,
            expected_challenge=session.get('registration_challenge'),
            expected_rp_id=current_app.config.get("RP_ID"),
            expected_origin=current_app.config.get("EXPECTED_ORIGIN"),
        )
    except Exception as e:
        current_app.logger.error(f'Registration response verification failed: {str(e)}')
        return jsonify({"status": "error", "message": str(e)}), 500
    
    user = User(
        username=username,
        credential_id=urlsafe_b64encode(registration_response.credential_id).decode("ascii").rstrip("=")    ,
        public_key=urlsafe_b64encode(registration_response.credential_public_key).decode("ascii").rstrip("="),
    )
    db.session.add(user)
    db.session.commit()

    session.pop("registration_challenge", None)
    session.pop("registration_username", None)
    return jsonify({"status": "success"})
