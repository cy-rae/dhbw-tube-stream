"""Service for streaming videos and receiving related metadata."""
import os

from flask import Flask
from flask_cors import CORS

from app.models.video_metadata import db
from app.routes.health_check_routes import health_check_api
from app.routes.metadata_routes import metadata_api
from app.routes.streaming_routes import streaming_api


def create_app():
    # Create the Flask app
    app = Flask(__name__)

    # Enable CORS for the frontend
    frontend_base_url = os.getenv('FRONTEND_BASE_URL', 'http://frontend-service:80')
    CORS(app, resources={
        r"/*": {
            "origins": [
                frontend_base_url
            ]
        }
    })

    # Set environment variables for connection to PostgreSQL database
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize the database
    db.init_app(app)

    # Register blueprints
    app.register_blueprint(streaming_api)
    app.register_blueprint(metadata_api)
    app.register_blueprint(health_check_api)

    return app
