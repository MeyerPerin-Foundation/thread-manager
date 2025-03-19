from flask import Blueprint, render_template

from content.birds import BirdContent
from content.too_far import TooFarContent
from content.ungovernable import UngovernableContent
from content.folder.folder_content import FolderContent
from .dashboard_db import DashboardDB
from social_media import Bluesky

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")

@dashboard_bp.route("/", methods=["GET"])
def dashboard():
    data_snapshot()

    dash = DashboardDB()
    dash_data = dash.latest_dashboard_data()

    return render_template("dashboard.html", data_payload=dash_data)


@dashboard_bp.route("/take_data_snapshot", methods=["POST"])
def data_snapshot():
    payload = {}

    dash = DashboardDB()
    birds = BirdContent()
    bsky = Bluesky()

    # Combine the data into a single payload
    payload.update(birds.count_birds())
    payload.update({"threads_followers": -1})
    payload.update({"bluesky_followers": bsky.get_follower_count()})

    dash.update_dashboard(payload)

    return "OK", 200
