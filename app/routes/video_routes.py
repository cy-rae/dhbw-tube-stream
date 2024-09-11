"""
Routes for video metadata and video streaming.
"""
from flask import Blueprint, jsonify, request, Response
from datetime import datetime
import re

from minio import S3Error

from app.models.minio_client import minio_client
from app.models.video_metadata import db, VideoMetadata
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
video_api = Blueprint(name='video_api', import_name=__name__)

video_bucket_name = "video-files"


@video_api.route('/video/<video_id>', methods=['GET'])
def get_video_metadata(video_id):
    """Returns the metadata of a video based on the video ID"""
    video_metadata = VideoMetadata.query.get(video_id)
    if video_metadata:
        return jsonify(video_metadata.to_json()), 200
    else:
        return jsonify({'error': 'Video not found'}), 404


@video_api.route('/video/stream/<video_id>', methods=['GET'])
def stream_video(video_id):
    """Streams the video based on the video ID"""
    video = VideoMetadata.query.get(video_id)
    if not video:
        return jsonify({'error': 'Video not found.'}), 404

    try:
        # Hole Metadaten des Objekts (z.B. Dateigröße)
        stat = minio_client.stat_object(video_bucket_name, video.video_filename)
        file_size = stat.size

        # Hole das Video-Objekt von MinIO
        response = minio_client.get_object(video_bucket_name, video.video_filename)

        # Range-Header prüfen
        range_header = request.headers.get('Range')
        if range_header:
            match = re.match(r'bytes=(\d+)-(\d*)', range_header)
            if match:
                byte1 = int(match.group(1))
                byte2 = int(match.group(2)) if match.group(2) else file_size - 1
                length = byte2 - byte1 + 1

                # Daten für den Range-Request extrahieren
                response_data = response.read()[byte1:byte2 + 1]
                headers = {
                    'Content-Range': f'bytes {byte1}-{byte2}/{file_size}',
                    'Accept-Ranges': 'bytes',
                    'Content-Length': str(length),
                    'Content-Type': video.video_mime_type,
                    'Content-Disposition': f'inline; filename={video.video_filename}'
                }
                return Response(response_data, status=206, headers=headers)
        else:
            # Kein Range-Request, ganzes Video senden
            headers = {
                'Content-Length': str(file_size),
                'Content-Type': video.video_mime_type,
                'Content-Disposition': f'inline; filename={video.video_filename}'
            }
            return Response(response, headers=headers)

    except S3Error as e:
        logging.critical(str(e))
        return jsonify({'error': f'S3 Error: {str(e)}'}), 500
    except Exception as e:
        logging.critical(str(e))
        return jsonify({'error': f'Internal Server Error: {str(e)}'}), 500


@video_api.route('/videos/search', methods=['GET'])
def search_videos():
    """Search for videos based on various filters like title, creator, and upload date."""
    # Extract query parameters
    title = request.args.get('title')
    creator = request.args.get('creator')
    upload_date = request.args.get('upload_date')
    sort_by = request.args.get('sort_by', 'upload_date')  # Default sorting by upload date
    order = request.args.get('order', 'asc')  # Default order ascending
    page = request.args.get('page', 1, type=int)  # Default page number is 1
    per_page = request.args.get('per_page', 10, type=int)  # Default items per page is 10

    # Start with base query
    query, error_message = create_filter_query(title, creator, upload_date, sort_by, order)
    if query is None:
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


def create_filter_query(title: str or None, creator: str or None, upload_date: str or None, sort_by: str,
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
