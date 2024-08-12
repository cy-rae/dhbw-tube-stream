"""Endpoint for reading video related data and streaming from MinIO"""

from flask import Blueprint, jsonify, request, Response
from .models import db, Video
from minio import Minio
import os

streaming_api = Blueprint(name='streaming_api', import_name=__name__)

# MinIO Client Setup
minio_client = Minio(
    os.getenv('MINIO_ENDPOINT', 'minio:9000'),
    access_key=os.getenv('MINIO_ACCESS_KEY', 'minioadmin'),
    secret_key=os.getenv('MINIO_SECRET_KEY', 'minioadmin'),
    secure=False
)

bucket_name = "video-files"

@streaming_api.route(rule='/videos', methods=['GET'])
def list_videos():
    """Returns a list of all video IDs"""
    videos = Video.query.with_entities(Video.id).all()
    video_ids = [video.id for video in videos]
    return jsonify(video_ids), 200

@streaming_api.route('/video/<video_id>', methods=['GET'])
def get_video_metadata(video_id):
    """Returns the metadata of a video based on the video ID"""
    video = Video.query.get(video_id)
    if video:
        return jsonify({
            'id': video.id,
            'title': video.title,
            'creator': video.creator,
            'description': video.description,
            'upload_date': video.upload_date
        }), 200
    else:
        return jsonify({'error': 'Video not found'}), 404

@streaming_api.route('/video/stream/<video_id>', methods=['GET'])
def stream_video(video_id):
    """Streams the video based on the video ID"""
    video = Video.query.get(video_id)
    if not video:
        return jsonify({'error': 'Video not found'}), 404

    try:
        response = minio_client.get_object(bucket_name, video.filename)
        return Response(response.stream(32*1024),
                        content_type='video/mp4',
                        headers={"Content-Disposition": f"inline; filename={video.filename}"})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
