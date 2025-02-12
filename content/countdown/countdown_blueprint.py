from flask import Blueprint, request
from content.countdown import CountdownContent

countdown_bp = Blueprint('countdown', __name__, url_prefix='/countdown')

@countdown_bp.route("/post_midterms", methods=["POST"])
def post_midterms():
    c = CountdownContent()

    # if there's any json data in the request, get its after_utc
    after_utc = request.json.get("after_utc", None)    
    if after_utc:
        d = c.queue_midterms_countdown(after_utc=after_utc)
        return "Accepted", 202

    d = c.post_midterms_countdown()
    if d:
        return d.result()
    else:
        return "No content", 204