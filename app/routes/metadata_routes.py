"""
Routes for video metadata and video streaming.
"""
import logging
from datetime import datetime

from flask import Blueprint, jsonify, request

from app.models.video_metadata import db, VideoMetadata

metadata_api = Blueprint(name='metadata_api', import_name=__name__)
logging.basicConfig(level=logging.INFO)


@metadata_api.route('/video/<video_id>', methods=['GET'])
def get_video_metadata(video_id):
    """Returns the metadata of a video based on the video ID"""
    video_metadata = VideoMetadata.query.get(video_id)
    if video_metadata:
        return jsonify(video_metadata.to_json()), 200
    else:
        return jsonify({'error': 'Video not found'}), 404


@metadata_api.route('/videos/search', methods=['GET'])
def search_videos():
    """Search for videos based on various filters like title, creator, and upload date."""
    # Extract query parameters
    title = request.args.get('title')
    creator = request.args.get('creator')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    sort_by = request.args.get('sort_by', 'upload_date')  # Default sorting by upload date
    order = request.args.get('order', 'asc')  # Default order ascending
    page = request.args.get('page', 1, type=int)  # Default page number is 1
    per_page = request.args.get('per_page', 10, type=int)  # Default items per page is 10

    # Start with base query
    query, error_message = create_filter_query(title, creator, start_date, end_date, sort_by, order)
    if query is None:
        logging.critical(error_message)
        return jsonify({'error': error_message}), 400

    # Apply pagination
    paginated_results = query.paginate(page=page, per_page=per_page, error_out=False)

    # Convert video metadata to dictionary
    videos = [video.to_json_as_listing() for video in paginated_results.items]

    # Return results with pagination metadata
    return jsonify({
        'videos': videos,
        'total': paginated_results.total,
        'pages': paginated_results.pages,
        'current_page': paginated_results.page,
        'per_page': paginated_results.per_page
    }), 200


def create_filter_query(title: str or None, creator: str or None, start_date: str or None, end_date: str or None,
                        sort_by: str,
                        order: str) -> (db.Query or None, str):
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
    if start_date and end_date:
        try:
            # Convert strings to datetime objects with timezone
            start_date_obj = datetime.fromisoformat(start_date)
            end_date_obj = datetime.fromisoformat(end_date)
            # Filter by date range in UTC
            query = query.filter(VideoMetadata.upload_date.between(start_date_obj, end_date_obj))
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
