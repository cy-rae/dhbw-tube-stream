"""Endpoint for reading video related data and streaming from MinIO"""

from flask import Blueprint, jsonify, request, Response, send_file

from app.models.video_metadata import db, VideoMetadata
from minio import Minio
from datetime import datetime
import os
from io import BytesIO

streaming_api = Blueprint(name='streaming_api', import_name=__name__)

# MinIO Client Setup
minio_client = Minio(
    os.getenv('MINIO_ENDPOINT', 'minio:9000'),
    access_key=os.getenv('MINIO_ACCESS_KEY', 'minioadmin'),
    secret_key=os.getenv('MINIO_SECRET_KEY', 'minioadmin'),
    secure=False
)

video_bucket_name = "video-files"
cover_bucket_name = "video-covers"

video_not_found = 'Video not found.'


@streaming_api.route('/video/<video_id>', methods=['GET'])
def get_video_metadata(video_id):
    """Returns the metadata of a video based on the video ID"""
    video_metadata = VideoMetadata.query.get(video_id)
    if video_metadata:
        return jsonify({
            'id': video_metadata.id,
            'title': video_metadata.title,
            'creator': video_metadata.creator,
            'description': video_metadata.description,
            'upload_date': video_metadata.upload_date
        }), 200
    else:
        return jsonify({'error': video_not_found}), 404


@streaming_api.route('/video/stream/<video_id>', methods=['GET'])
def stream_video(video_id):
    """Streams the video based on the video ID"""
    video = VideoMetadata.query.get(video_id)
    if not video:
        return jsonify({'error': video_not_found}), 404

    try:
        response = minio_client.get_object(video_bucket_name, video.video_filename)
        return Response(response.stream(32 * 1024),
                        headers={"Content-Disposition": f"inline; filename={video.video_filename}"})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@streaming_api.route('/video/cover/<video_id>', methods=['GET'])
def get_video_cover(video_id):
    """Returns the cover image of a video based on the video ID"""
    video = VideoMetadata.query.get(video_id)
    if not video:
        return jsonify({'error': video_not_found}), 404

    try:
        response = minio_client.get_object(cover_bucket_name, video.cover_filename)
        # Reading the image into memory and returning it
        image_data = BytesIO(response.read())
        return send_file(image_data, as_attachment=False, download_name=video.cover_filename)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@streaming_api.route('/videos/search', methods=['GET'])
def search_videos():
    """Search for videos based on various filters like title, creator, and upload date."""
    # Extract query parameters
    title = request.args.get('title')
    creator = request.args.get('creator')
    upload_date = request.args.get('upload_date')
    description = request.args.get('description')
    sort_by = request.args.get('sort_by', 'upload_date')  # Default sorting by upload date
    order = request.args.get('order', 'asc')  # Default order ascending
    page = request.args.get('page', 1, type=int)  # Default page number is 1
    per_page = request.args.get('per_page', 10, type=int)  # Default items per page is 10

    # Start with base query
    query = VideoMetadata.query

    # Apply filters
    if title:
        query = query.filter(VideoMetadata.title.ilike(f'%{title}%'))
    if creator:
        query = query.filter(VideoMetadata.creator.ilike(f'%{creator}%'))
    if description:
        query = query.filter(VideoMetadata.description.ilike(f'%{description}%'))
    if upload_date:
        try:
            # Convert string to datetime object
            upload_date_obj = datetime.strptime(upload_date, '%Y-%m-%d')
            query = query.filter(db.func.date(VideoMetadata.upload_date) == upload_date_obj.date())
        except ValueError:
            return jsonify({'error': 'Invalid date format. Please use YYYY-MM-DD.'}), 400

    # Apply sorting
    if sort_by in ['title', 'creator', 'upload_date']:
        if order == 'desc':
            query = query.order_by(getattr(VideoMetadata, sort_by).desc())
        else:
            query = query.order_by(getattr(VideoMetadata, sort_by).asc())
    else:
        return jsonify({'error': f'Invalid sort_by field: {sort_by}'}), 400

    # Apply pagination
    paginated_results = query.paginate(page=page, per_page=per_page, error_out=False)

    # Convert video metadata to dictionary
    videos = [video.to_dict() for video in paginated_results.items]

    # Return results with pagination metadata
    return jsonify({
        # 'videos': video_ids,
        'videos': videos,
        'total': paginated_results.total,
        'pages': paginated_results.pages,
        'current_page': paginated_results.page,
        'per_page': paginated_results.per_page
    }), 200
