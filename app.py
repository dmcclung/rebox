from flask import Flask, request, jsonify, session, render_template
from webauthn import generate_registration_options, verify_registration_response
from webauthn import generate_authentication_options, verify_authentication_response
from webauthn.helpers.structs import PublicKeyCredentialDescriptor, AuthenticatorSelection, ResidentKeyRequirement, UserVerificationRequirement

import psycopg2
from psycopg2.extras import RealDictCursor

from dotenv import load_dotenv
load_dotenv()

import os
import base64
import json

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

users = {}

def get_db_connection():
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    conn.cursor(cursor_factory=RealDictCursor)
    return conn

@app.route("/", methods=["GET"])
def index():
    if 'username' in session:
        return render_template("emails.html")
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login():
    username = request.json["username"]
    if username not in users:
        return jsonify({"error": "User not found"}), 404
    
    credential_id = base64.urlsafe_b64decode(users[username]["credential_id"])
    authentication_options = generate_authentication_options(
        rp_id=os.getenv("RP_ID"),
        allow_credentials=[
            PublicKeyCredentialDescriptor(
                id=credential_id,
                type="public-key",
            )
        ],
    )

    session['authentication_challenge'] = authentication_options['challenge']
    session['username'] = username
    return jsonify(json.loads(authentication_options.json()))

@app.route("/authenticate", methods=["POST"])
def authenticate():
    username = session['username']
    if not username:
        return jsonify({"error": "No authentication in progress"}), 404
    try:
        credential_id = base64.urlsafe_b64decode(users[username]["credential_id"])
        public_key = base64.urlsafe_b64decode(users[username]["public_key"])
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
    if not username or username in users:
        return jsonify({"status": "error", "message": "Invalid or existing username"}), 400
    
    registration_options = generate_registration_options(
        rp_id=os.getenv("RP_ID"),
        rp_name=os.getenv("RP_NAME"),
        user_id=username.encode("utf-8"),
        user_name=username,
        user_display_name=username,
        attestation="none",
        authenticator_selection=AuthenticatorSelection(
            resident_key=ResidentKeyRequirement.REQUIRED,
            user_verification=UserVerificationRequirement.REQUIRED,
        ),
    )

    session['registration_challenge'] = registration_options['challenge']
    session['username'] = username

    return jsonify(json.loads(registration_options.json()))

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
    
    users[username] = {
        "credential_id": base64.urlsafe_b64encode(registration_response.credential_id).decode("utf-8"),
        "public_key": base64.urlsafe_b64encode(registration_response.public_key).decode("utf-8"),
    }

    session.pop("registration_challenge")
    session.pop("username")
    return jsonify({"status": "success"})

@app.route("/emails", methods=["GET"])
def emails():
    if 'username' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM emails WHERE username = %s', (session['username'],))
            emails = cursor.fetchall()
            return jsonify(emails)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route("/logout", methods=["POST"])
def logout():
    session.pop("username")
    return jsonify({"status": "success"})

if __name__ == "__main__":
    app.run(ssl_context="adhoc")