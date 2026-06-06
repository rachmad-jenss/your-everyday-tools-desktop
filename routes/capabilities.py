from flask import Blueprint, jsonify

from utils.capabilities import get_capabilities

bp = Blueprint("capabilities", __name__)


@bp.route("/capabilities")
def capabilities():
    return jsonify(get_capabilities())
