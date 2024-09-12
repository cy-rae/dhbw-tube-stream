"""
This module contains the routes for streaming video files and cover images.
"""
from flask import Blueprint, jsonify, request, Response
import re
from minio import S3Error
import logging

from app.models.minio_client import minio_client
from app.models.video_metadata import VideoMetadata

streaming_api = Blueprint(name='streaming_api', import_name=__name__)
logging.basicConfig(level=logging.INFO)
video_bucket_name = "video-files"
cover_bucket_name = "video-covers"


@streaming_api.route('/cover/<video_id>', methods=['GET'])
def stream_cover(video_id) -> tuple[Response, int] | Response:
    """Streams the cover image based on the video ID"""
    video = VideoMetadata.query.get(video_id)
    if not video:
        return jsonify({'error': 'Video not found.'}), 404

    return stream_file(bucket_name=cover_bucket_name, filename=video.cover_filename, mime_type=video.cover_mime_type)


@streaming_api.route('/video/stream/<video_id>', methods=['GET'])
def stream_video(video_id) -> tuple[Response, int] | Response:
    """Streams the video based on the video ID"""
    video = VideoMetadata.query.get(video_id)
    if not video:
        return jsonify({'error': 'Video not found.'}), 404

    return stream_file(bucket_name=video_bucket_name, filename=video.video_filename, mime_type=video.video_mime_type)


def stream_file(bucket_name: str, filename: str, mime_type: str) -> Response | tuple[Response, int]:
    """
    Streams the file from MinIO based on the bucket name and filename.
    """
    try:
        # Get metadata of the file
        stat = minio_client.stat_object(bucket_name, filename)
        file_size = stat.size

        # Get file from MinIO
        response = minio_client.get_object(bucket_name, filename)

        # Check range header
        range_header = request.headers.get('Range')
        if range_header:
            match = re.match(r'bytes=(\d+)-(\d*)', range_header)
            if match:
                byte1 = int(match.group(1))
                byte2 = int(match.group(2)) if match.group(2) else file_size - 1
                length = byte2 - byte1 + 1

                # Extract data for the range request
                response_data = response.read()[byte1:byte2 + 1]
                headers = {
                    'Content-Range': f'bytes {byte1}-{byte2}/{file_size}',
                    'Accept-Ranges': 'bytes',
                    'Content-Length': str(length),
                    'Content-Type': mime_type,
                    'Content-Disposition': f'inline; filename={filename}'
                }
                return Response(response_data, status=206, headers=headers)
        else:
            # No range header, return full video
            headers = {
                'Content-Length': str(file_size),
                'Content-Type': mime_type,
                'Content-Disposition': f'inline; filename={filename}'
            }
            return Response(response, headers=headers)
    except S3Error as e:
        logging.critical(str(e))
        return jsonify({'error': f'S3 Error: {str(e)}'}), 500
    except Exception as e:
        logging.critical(str(e))
        return jsonify({'error': f'Internal Server Error: {str(e)}'}), 500
