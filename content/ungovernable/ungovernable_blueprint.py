from flask import Blueprint, request
from content.ungovernable import UngovernableContent

ungov_bp = Blueprint('ungov', __name__, url_prefix='/ungov')

@ungov_bp.route("/post_ungovernable", methods=["POST"])
def post_ungovernable():
    u = UngovernableContent()

    # if there's any json data in the request, get its after_utc
    after_utc = request.json.get("after_utc", None)
    if after_utc:
        d = u.queue_ungovernable(after_utc=after_utc)
        return "Accepted", 202


    d = u.post_ungovernable()
    if d:
        return d.result()
    else:
        return "No content", 204

