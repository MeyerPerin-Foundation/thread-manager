from flask import Blueprint
from content.too_far import TooFarContent

too_far_bp = Blueprint('too_far', __name__, url_prefix='/too_far')

@too_far_bp.route("/post_too_far", methods=["POST"])
def post_too_far():

    f = TooFarContent()
    d = f.post_too_far()
    if d:
        return d.result()
    else:
        return "No content", 204