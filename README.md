# dhbw-tube-stream Microservice

## Overview
The **DHBW Tube Stream Microservice** is a Flask-based application designed to handle video streaming and metadata retrieval. It provides endpoints for streaming video files and cover images from MinIO object storage, as well as retrieving video metadata from a PostgreSQL database. This microservice ensures efficient and secure access to video content and its associated metadata.

## Features
- **Video Streaming**: Streams video files directly from MinIO object storage.
- **Cover Image Streaming**: Streams cover images (thumbnails) associated with videos.
- **Metadata Retrieval**: Retrieves video metadata from a PostgreSQL database.
- **Range Requests**: Supports HTTP range requests for efficient video streaming.
- **Error Handling**: Provides detailed error messages and logging for troubleshooting.
- **Caching**: A memcache client is being used to cache video metadata to improve performance.
The caching mechanism is only used to store video metadata (`/video/<video_id>`) because the files are streamed directly from MinIO which is already optimized for performance.

## Endpoints
`/video/<video_id>`
- Method: GET
- Description: Returns the metadata of a video based on the video ID.
- Response:
    - *200 OK*: If the metadata is successfully retrieved.
    - *404 Not Found*: If the video is not found.

`/videos/search`
- Method: GET
- Description: Searches for videos based on various filters like title, creator, and upload date.
- Query Parameters:
    - `title` (string, optional): Filter by video title.
    - `creator` (string, optional): Filter by video creator.
    - `start_date` (string, optional): Filter by upload start date (YYYY-MM-DD).
    - `end_date` (string, optional): Filter by upload end date (YYYY-MM-DD).
    - `sort_by` (string, optional): Field to sort by (default: upload_date).
    - `order` (string, optional): Sort order (asc or desc, default: asc).
    - `page` (int, optional): Page number for pagination (default: 1).
    - `per_page` (int, optional): Number of items per page (default: 10).
- Response:
    - *200 OK*: If the search is successful.
    - *400 Bad Request*: If the query parameters are invalid.

`/cover/<video_id>`
- Method: GET
- Description: Streams the cover image based on the video ID.
- Response:
    - *200 OK*: If the cover image is successfully streamed.
    - *404 Not Found*: If the video is not found.

`/video/stream/<video_id>`
- Method: GET
- Description: Streams the video based on the video ID.
- Response:
    - *200 OK*: If the video is successfully streamed.
    - *206 Partial Content*: If a range request is made.
    - *404 Not Found*: If the video is not found.

## Configuration
The microservice can be configured using environment variables. The following variables are available:

- `FLASK_APP`: The Flask application entry point.
- `FLASK_ENV`: The environment in which the Flask app is running (e.g., production).
- `MINIO_ENDPOINT`: The endpoint for the MinIO server.
- `MINIO_ACCESS_KEY`: The access key for MinIO.
- `MINIO_SECRET_KEY`: The secret key for MinIO.
- `POSTGRES_URI`: The URI for the PostgreSQL database.
- `MEMCACHED_HOST`: The host for the Memcached server.
- `MEMCACHED_PORT`: The port for the Memcached server.

## Logging
The microservice uses Python's built-in logging module to log important events and errors. Logs are printed to the console and can be viewed in the Docker container logs.
