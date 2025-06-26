from flask import Blueprint, jsonify, session, request, current_app
import webauthn as webauthn
from webauthn.helpers.structs import (
    AttestationConveyancePreference, 
    AuthenticatorAttachment, 
    AuthenticatorSelectionCriteria,
    UserVerificationRequirement,
    PublicKeyCredentialDescriptor
)
import json
from db import db
from models import User

bp = Blueprint('auth', __name__)

@bp.route('/generate-authentication-options', methods=['POST'])
def generate_authentication_options():
    username = request.json["username"]
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    credential_id = webauthn.base64url_to_bytes(user.credential_id)
    authentication_options = webauthn.generate_authentication_options(
        rp_id=current_app.config.get("RP_ID"),
        allow_credentials=[PublicKeyCredentialDescriptor(id=credential_id)],
        user_verification=UserVerificationRequirement.PREFERRED,
    )

    session['authentication_challenge'] = authentication_options.challenge
    session['authentication_username'] = username
    return jsonify(json.loads(webauthn.options_to_json(authentication_options)))

@bp.route('/verify-authentication', methods=['POST'])
def verify_authentication():
    username = session.get('authentication_username')
    if not username:
        return jsonify({"error": "No authentication in progress"}), 404
    try:
        user = User.query.filter_by(username=username).first()
        public_key = webauthn.base64url_to_bytes(user.public_key)
        webauthn.verify_authentication_response(
            credential=request.json,
            expected_challenge=session.get('authentication_challenge'),
            expected_rp_id=current_app.config.get("RP_ID"),
            expected_origin=current_app.config.get("EXPECTED_ORIGIN"),
            credential_current_sign_count=0,
            credential_public_key=public_key,
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    
    session.pop("authentication_challenge", None)
    session.pop("authentication_username", None)
    session['username'] = username
    
    return jsonify({"status": "success"})

@bp.route('/generate-registration-options', methods=['POST'])
def generate_registration_options():
    username = request.json["username"]
    if not username or User.query.filter_by(username=username).first():
        return jsonify({"status": "error", "message": "Invalid or existing username"}), 400
    
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
        return jsonify({"status": "error", "message": str(e)}), 400
    
    user = User(
        username=username,
        credential_id=webauthn.base64url_to_bytes(registration_response.credential_id).decode("utf-8"),
        public_key=webauthn.base64url_to_bytes(registration_response.credential_public_key).decode("utf-8"),
    )
    db.session.add(user)
    db.session.commit()

    session.pop("registration_challenge", None)
    session.pop("registration_username", None)
    return jsonify({"status": "success"})
