from flask import Blueprint, request
from content.countdown import CountdownContent

countdown_bp = Blueprint('countdown', __name__, url_prefix='/countdown')

@countdown_bp.route("/post_midterms", methods=["POST"])
def post_midterms():

    c = CountdownContent()
    d = c.post_midterms_countdown()
    if d:
        return d.result()
    else:
        return "No content", 204