"""
Routes for video metadata and video streaming.
"""
from flask import Blueprint, jsonify, request, Response
from datetime import datetime

from app.models.minio_client import minio_client
from app.models.video_metadata import db, VideoMetadata

video_api = Blueprint(name='video_api', import_name=__name__)

video_bucket_name = "video-files"


@video_api.route('/video/stream/<video_id>', methods=['GET'])
def stream_video(video_id):
    """Streams the video based on the video ID"""
    video = VideoMetadata.query.get(video_id)
    if not video:
        return jsonify({'error': 'Video not found.'}), 404

    try:
        response = minio_client.get_object(video_bucket_name, video.video_filename)
        return Response(response.stream(32 * 1024),
                        headers={"Content-Disposition": f"inline; filename={video.video_filename}"})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@video_api.route('/videos/search', methods=['GET'])
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
    query, error_message = create_filter_query(title, creator, upload_date, description, sort_by, order)
    if query is None:
        return jsonify({'error': f'Invalid sort_by field: {sort_by}'}), 400

    # Apply pagination
    paginated_results = query.paginate(page=page, per_page=per_page, error_out=False)

    # Convert video metadata to dictionary
    videos = [video.to_dict() for video in paginated_results.items]

    # Return results with pagination metadata
    return jsonify({
        'videos': videos,
        'total': paginated_results.total,
        'pages': paginated_results.pages,
        'current_page': paginated_results.page,
        'per_page': paginated_results.per_page
    }), 200


def create_filter_query(title: str or None, creator: str or None, upload_date: str or None, description: str or None,
                        sort_by: str, order: str) -> (db.Query or None, str):
    """
    Create a video metadata query based on the provided filters.
    """
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
            return None, 'Invalid date format. Please use YYYY-MM-DD.'

    # Apply sorting
    if sort_by in ['title', 'creator', 'upload_date']:
        if order == 'desc':
            query = query.order_by(getattr(VideoMetadata, sort_by).desc())
        else:
            query = query.order_by(getattr(VideoMetadata, sort_by).asc())
    else:
        return None, f'Invalid sort_by field: {sort_by}'

    return query, ''
