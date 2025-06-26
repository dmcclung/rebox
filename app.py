from flask import Flask
import os
from db import db
from migrate import migrate

from dotenv import load_dotenv
load_dotenv()

def create_app():
    # Create and configure the app
    app = Flask(__name__)
    
    # Load configuration from environment variables
    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY"),
        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        RP_ID=os.getenv("RP_ID"),
        RP_NAME=os.getenv("RP_NAME"),
        EXPECTED_ORIGIN=os.getenv("EXPECTED_ORIGIN")
    )

    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)

    # Initialize database
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        
    # Register all routes
    from routes import register_routes
    register_routes(app)

    return app

app = create_app()

if __name__ == "__main__":
    app.run(ssl_context="adhoc")