from flask import Blueprint, jsonify

health_check_api = Blueprint(name='health_check_api', import_name=__name__)


@health_check_api.route('/health', methods=['GET'])
def check_health():
    return jsonify(status="healthy"), 200
