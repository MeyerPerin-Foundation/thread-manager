from flask import Blueprint, render_template

from utils.cosmosdb.birds import BirdsDB
from utils.cosmosdb.dashboard import DashboardDB
from utils.cosmosdb.too_far import TooFarDB
from utils.cosmosdb.ungovernable import UngovernableDB
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

    birds = BirdsDB()
    ungov = UngovernableDB()
    too_far = TooFarDB()
    dash = DashboardDB()
    bsky = Bluesky()

    # Combine the data into a single payload
    payload.update(birds.count_birds())
    payload.update(ungov.count_ungovernable())
    payload.update(too_far.count_too_far())
    payload.update({"threads_followers": -1})
    payload.update({"bluesky_followers": bsky.get_follower_count()})

    dash.update_dashboard(payload)

    return "OK", 200
