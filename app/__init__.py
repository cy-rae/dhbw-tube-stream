"""Service for streaming videos and receiving related metadata."""

from flask import Flask
from flask_cors import CORS

from app.models.video_metadata import db
from app.routes.health_check_routes import health_check_api
from app.routes.metadata_routes import metadata_api
from app.routes.streaming_routes import streaming_api


def create_app():
    app = Flask(__name__)

    CORS(app, resources={r"/*": {"origins": "http://frontend-service"}})

    # Connection to PostgreSQL database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:password@postgres:5432/videos'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    # Register blueprints
    app.register_blueprint(streaming_api)
    app.register_blueprint(metadata_api)
    app.register_blueprint(health_check_api)

    return app
