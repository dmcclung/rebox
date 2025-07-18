from flask import Flask, current_app
from flask_login import LoginManager, current_user
import os
from datetime import timedelta
from db import db
from migrate import migrate
from models import User, Email, EmailAlias, Attachment

from dotenv import load_dotenv
load_dotenv()

def create_app():
    # Create and configure the app
    app = Flask(__name__)
    
    # Configure logging to show immediately in Docker
    import sys
    import logging
    from logging.handlers import RotatingFileHandler
    
    # Set up logging to console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    
    # Clear any existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add console handler to root logger
    root_logger.addHandler(console_handler)
    root_logger.setLevel(logging.DEBUG)
    
    # Enable SQLAlchemy logging
    logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
    
    # Load configuration from environment variables
    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY"),
        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        
        # Session configuration
        SESSION_COOKIE_SECURE=os.getenv('FLASK_ENV') == 'production',
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        PERMANENT_SESSION_LIFETIME=timedelta(days=7),
        SESSION_REFRESH_EACH_REQUEST=True,
        
        # Remember me configuration
        REMEMBER_COOKIE_SECURE=os.getenv('FLASK_ENV') == 'production',
        REMEMBER_COOKIE_HTTPONLY=True,
        REMEMBER_COOKIE_SAMESITE='Lax',
        REMEMBER_COOKIE_DURATION=timedelta(days=30),
        
        # CSRF protection
        WTF_CSRF_ENABLED=True,
        
        # Ensure session is saved on every request
        SESSION_PROTECTION='strong',
        
        RP_ID=os.getenv("RP_ID"),
        RP_NAME=os.getenv("RP_NAME"),
        EXPECTED_ORIGIN=os.getenv("EXPECTED_ORIGIN"),
        EMAIL_DOMAIN=os.getenv("EMAIL_DOMAIN", "rebox.sh"),  # Default to rebox.sh if not set
        SMTP_SERVER=os.getenv("SMTP_SERVER"),
        SMTP_PORT=int(os.getenv("SMTP_PORT", 587)),
        SMTP_USERNAME=os.getenv("SMTP_USERNAME"),
        SMTP_PASSWORD=os.getenv("SMTP_PASSWORD"),
    )

    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login_page'

    @login_manager.user_loader
    def load_user(user_id):
        user = User.query.get(int(user_id))
        current_app.logger.debug(f"[DEBUG] Loading user - id: {user_id}, found: {user is not None}")
        return user

    # Initialize database
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        
    # Register all routes
    from routes import register_routes
    register_routes(app)

    @app.context_processor
    def inject_primary_email():
        """Inject the user's primary email into the template context."""
        if current_user.is_authenticated:
            email_domain = current_app.config.get('EMAIL_DOMAIN', 'rebox.sh')
            primary_email = f"{current_user.username}@{email_domain}"
            return dict(primary_email=primary_email)
        return dict(primary_email=None)

    return app

app = create_app()

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, port=5000)