"""
This module contains the routes for streaming video files and cover images.
"""
import logging
import re

from flask import Blueprint, jsonify, request, Response, stream_with_context
from minio import S3Error

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
        logging.error("Video not found.")
        return jsonify({'error': 'Video not found.'}), 404

    return stream_file(
        bucket_name=cover_bucket_name,
        filename=video.cover_filename,
        mime_type=video.cover_mime_type
    )


@streaming_api.route('/video/stream/<video_id>', methods=['GET'])
def stream_video(video_id) -> tuple[Response, int] | Response:
    """Streams the video based on the video ID"""
    video = VideoMetadata.query.get(video_id)
    if not video:
        logging.error("Video not found.")
        return jsonify({'error': 'Video not found.'}), 404

    return stream_file(
        bucket_name=video_bucket_name,
        filename=video.video_filename,
        mime_type=video.video_mime_type
    )


def stream_file(bucket_name: str, filename: str, mime_type: str) -> Response | tuple[Response, int]:
    # Get file size
    file_stat_object = minio_client.stat_object(bucket_name, filename)
    file_size: int = file_stat_object.size

    # Get range header
    range_header = request.headers.get('Range', None)
    if range_header:
        # Get the requested byte range
        range_match = re.search(r'bytes=(\d+)-(\d*)', range_header)
        if range_match:
            start, end = range_match.groups()
            start = int(start)
            end = int(end) if end else None  # If end is None, it means the end of the file

            # Create streaming response
            response = Response(
                stream_with_context(stream_file_chunk(bucket_name, filename, file_size, start, end)),
                status=206,  # 206 Partial Content
                content_type=mime_type,
                headers={
                    'Content-Range': f'bytes {start}-{end}/{file_size}',
                    'Accept-Ranges': 'bytes',
                },
            )
            return response
        else:
            return jsonify({'error': 'Invalid Range'}), 416  # Range Not Satisfiable
    else:
        # If no range header is provided, stream the whole file
        return Response(
            stream_with_context(stream_file_chunk(bucket_name, filename, file_size, 0, None)),
            content_type=mime_type,
            direct_passthrough=True
        )


def stream_file_chunk(
        bucket_name: str,
        file_name: str,
        file_size: int,
        start: int,
        end: int = None,
        chunk_size=1024 * 1024
):
    """
    Generator function to stream a chunk of a file from MinIO.
    """
    try:
        # If end is None or greater than the file size, set it to the end of the file
        if end is None or end >= file_size:
            end = file_size - 1

        # Calculate the length of the requested chunk
        length = end - start + 1

        # Get the object from MinIO with the specified range and offset
        response = minio_client.get_object(bucket_name, file_name, offset=start, length=length)

        # Read the file in chunks and yield the chunks
        while True:
            chunk = response.read(chunk_size)
            if not chunk:
                break
            yield chunk

        # Close the MinIO response
        response.close()
    except S3Error as e:
        print(f"Fehler beim Abrufen des Objekts: {e}")
        raise
