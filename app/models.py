"""Definition of the database model to save the video and metadata."""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class VideoMetadata(db.Model):
    id = db.Column(db.String, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    creator = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    cover_filename = db.Column(db.String(120), nullable=False)
    video_filename = db.Column(db.String(120), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Video {self.title}>'
