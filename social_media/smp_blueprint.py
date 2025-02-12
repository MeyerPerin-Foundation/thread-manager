from flask import Blueprint, request, render_template
from social_media import SocialMediaPoster, SocialMediaScheduler

smp_bp = Blueprint("smp", __name__, url_prefix="/smp")


@smp_bp.route("/list", methods=["GET"])
def list_posts():

    poster = SocialMediaPoster()
    return render_template("post_queue.html", queue=poster.get_post_queue())


@smp_bp.route("/pop", methods=["POST"])
def post_from_queue():

    poster = SocialMediaPoster()
    d = poster.post_next_document()
    if d:
        return d.result()
    else:
        return "No content", 204

@smp_bp.route("/push", methods=["POST"])
def add_post_to_queue():

    text = request.json.get("text", "")
    service = request.json.get("service", "Bluesky")
    after_utc = request.json.get("after_utc", "2000-01-01T00:00:00Z")
    image_url = request.json.get("image_url", None)
    img_file = request.json.get("img_file", None)
    url = request.json.get("url", None)
    url_title = request.json.get("url_title", None)
    hashtags = request.json.get("hashtags", None)
    emojis = request.json.get("emojis", None) 

    poster = SocialMediaPoster()
    id = poster.generate_and_queue_document(
        text=text,
        service=service,
        after_utc=after_utc,
        image_url=image_url,
        img_file=img_file,
        url=url,
        url_title=url_title,
        hashtags=hashtags,
        emojis=emojis,
    )

    if d:
        return f"Accepted with id: {id}", 202
    else:
        return "No content", 204


@smp_bp.route("/tickle_scheduler", methods=["POST"])
def tickle_scheduler():

    scheduler = SocialMediaScheduler()
    
    schedule_items = scheduler.list_expired_schedules()
    ids = []
    for schedule in schedule_items:
        id = scheduler.generate_post_document(schedule)
        scheduler.update_schedule(schedule)
        if id:
            ids.append(id)

    if len(ids) > 0:
        return f"Accepted with ids: {ids}", 202
    else:
        return "No content", 204

