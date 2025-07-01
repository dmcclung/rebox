from .main import bp as main_bp
from .emails import bp as emails_bp
from .auth import bp as auth_bp
from .favicon import bp as favicon_bp
from .aliases import bp as aliases_bp

def register_routes(app):
    """Register all route blueprints with the Flask app"""
    app.register_blueprint(main_bp)
    app.register_blueprint(emails_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(favicon_bp)
    app.register_blueprint(aliases_bp)
