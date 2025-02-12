from flask import Blueprint, request
from content.ungovernable import UngovernableContent

ungov_bp = Blueprint('ungov', __name__, url_prefix='/ungov')

@ungov_bp.route("/post_ungovernable", methods=["POST"])
def post_ungovernable():

    u = UngovernableContent()
    d = u.post_ungovernable()
    if d:
        return d.result()
    else:
        return "No content", 204

