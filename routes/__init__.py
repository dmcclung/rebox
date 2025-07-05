from .ui import bp as ui_bp
from .emails import bp as emails_bp
from .auth import bp as auth_bp
from .aliases import bp as aliases_bp

def register_routes(app):
    """Register all route blueprints with the Flask app"""
    app.register_blueprint(ui_bp)
    app.register_blueprint(emails_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(aliases_bp)
