from flask import Flask, request, jsonify, session, render_template, send_from_directory, redirect, url_for
from webauthn import (
    generate_registration_options, 
    verify_registration_response,
    generate_authentication_options,
    verify_authentication_response,
    options_to_json
)
from webauthn.helpers.structs import (
    AttestationConveyancePreference, 
    AuthenticatorAttachment, 
    AuthenticatorSelectionCriteria,
    UserVerificationRequirement
)
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

from dotenv import load_dotenv
load_dotenv()

import os
import base64
import json

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    credential_id = db.Column(db.String(255), unique=True, nullable=False)
    public_key = db.Column(db.String(255), nullable=False)
    emails = db.relationship('Email', backref='user', lazy=True)

class Email(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(255), nullable=False)
    recipient = db.Column(db.String(255), nullable=False)
    subject = db.Column(db.String(255))
    body = db.Column(db.Text)
    received_at = db.Column(db.DateTime, server_default=db.func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Create tables if they don't exist
with app.app_context():
    db.create_all()

@app.route("/", methods=["GET"])
def index():
    if 'username' in session:
        return render_template("emails.html")
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login():
    username = request.json["username"]
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    credential_id = base64.urlsafe_b64decode(user.credential_id)
    authentication_options = generate_authentication_options(
        rp_id=os.getenv("RP_ID"),
        allow_credentials=[
            PublicKeyCredentialDescriptor(
                id=credential_id,
                type="public-key",
            )
        ],
    )

    session['authentication_challenge'] = authentication_options.challenge
    session['username'] = username
    return jsonify(json.loads(options_to_json(authentication_options)))

@app.route("/authenticate", methods=["POST"])
def authenticate():
    username = session['username']
    if not username:
        return jsonify({"error": "No authentication in progress"}), 404
    try:
        user = User.query.filter_by(username=username).first()
        credential_id = base64.urlsafe_b64decode(user.credential_id)
        public_key = base64.urlsafe_b64decode(user.public_key)
        verify_authentication_response(
            credential=request.json,
            expected_challenge=session['authentication_challenge'],
            expected_rp_id=os.getenv("RP_ID"),
            expected_origin=request.url_root,
            credential_public_key=public_key,
            credential_id=credential_id,
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    return jsonify({"status": "success"})

@app.route("/register", methods=["POST"])
def register():
    username = request.json["username"]
    if not username or User.query.filter_by(username=username).first():
        return jsonify({"status": "error", "message": "Invalid or existing username"}), 400
    
    registration_options = generate_registration_options(
        rp_id=os.getenv("RP_ID"),
        rp_name=os.getenv("RP_NAME"),
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
    session['username'] = username

    return jsonify(json.loads(options_to_json(registration_options)))

@app.route("/register/finish", methods=["POST"])
def register_finish():
    username = session['username']
    if not username:
        return jsonify({"error": "No registration in progress"}), 404
    try:
        registration_response = verify_registration_response(
            credential=request.json,
            expected_challenge=session['registration_challenge'],
            expected_rp_id=os.getenv("RP_ID"),
            expected_origin=request.url_root,
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    
    user = User(
        username=username,
        credential_id=base64.urlsafe_b64encode(registration_response.credential_id).decode("utf-8"),
        public_key=base64.urlsafe_b64encode(registration_response.public_key).decode("utf-8"),
    )
    db.session.add(user)
    db.session.commit()

    session.pop("registration_challenge")
    session.pop("username")
    return jsonify({"status": "success"})

@app.route("/emails", methods=["GET"])
def emails():
    if 'username' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    user = User.query.filter_by(username=session['username']).first()
    return jsonify([email.to_dict() for email in user.emails])

@app.route("/logout", methods=["GET"])
def logout():
    session.pop("username", None)
    return redirect(url_for('index'))

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static', 'images'),
                             'favicon.ico', mimetype='image/vnd.microsoft.icon')

if __name__ == "__main__":
    app.run(ssl_context="adhoc")