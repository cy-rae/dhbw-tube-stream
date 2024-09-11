"""
This module contains the routes for the cover API.
"""
from flask import Blueprint, jsonify, send_file
from io import BytesIO

from app.models.minio_client import minio_client
from app.models.video_metadata import VideoMetadata

cover_api = Blueprint(name='cover_api', import_name=__name__)

cover_bucket_name = "video-covers"


@cover_api.route('/cover/<video_id>', methods=['GET'])
def get_video_cover(video_id):
    """Returns the cover image of a video based on the video ID"""
    video = VideoMetadata.query.get(video_id)
    if not video:
        return jsonify({'error': 'Video not found.'}), 404

    try:
        response = minio_client.get_object(cover_bucket_name, video.cover_filename)
        # Reading the image into memory and returning it
        image_data = BytesIO(response.read())
        return send_file(image_data, as_attachment=False, download_name=video.cover_filename)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
