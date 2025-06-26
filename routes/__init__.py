from .main import bp as main_bp
from .emails import bp as emails_bp
from .webauthn import bp as webauthn_bp
from .user import bp as user_bp
from .favicon import bp as favicon_bp

def register_routes(app):
    """Register all route blueprints with the Flask app"""
    app.register_blueprint(main_bp)
    app.register_blueprint(emails_bp)
    app.register_blueprint(webauthn_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(favicon_bp)
