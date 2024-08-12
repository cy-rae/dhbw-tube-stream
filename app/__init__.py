"""Service for streaming videos and receiving related metadata."""

from flask import Flask
from .models import db
from .routes import streaming_api


def create_app():
    app = Flask(__name__)

    # Connection to PostgreSQL database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:password@postgres:5432/videos'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    app.register_blueprint(streaming_api)

    return app
