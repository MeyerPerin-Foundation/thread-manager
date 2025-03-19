from flask import Blueprint, request
from content.too_far import TooFarContent

too_far_bp = Blueprint('too_far', __name__, url_prefix='/too_far')

@too_far_bp.route("/post_too_far", methods=["POST"])
def post_too_far():

    f = TooFarContent()

    # if there's any json data in the request, get its after_utc
    after_utc = request.json.get("after_utc", None)

    if after_utc:
        d = f.generate_too_far(after_utc=after_utc)
        return "Accepted", 202

    d = f.post_too_far()
    if d:
        return d.result()
    else:
        return "No content", 204