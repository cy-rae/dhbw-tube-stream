from flask import Blueprint, jsonify

health_check_api = Blueprint(name='health_check_api', import_name=__name__)


@health_check_api.route('/health', methods=['GET'])
def get_video_metadata(video_id):
    return jsonify(status="healthy"), 200
