"""Service for streaming videos and receiving related metadata."""

from flask import Flask
from flask_cors import CORS

from app.models.video_metadata import db
from app.routes.cover_routes import cover_api
from app.routes.video_routes import video_api


def create_app():
    app = Flask(__name__)

    # TODO: Configure CORS correctly.
    CORS(app, resources={r"/*": {"origins": "http://localhost:5003"}})

    # Connection to PostgreSQL database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:password@postgres:5432/videos'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    app.register_blueprint(cover_api)
    app.register_blueprint(video_api)

    return app
