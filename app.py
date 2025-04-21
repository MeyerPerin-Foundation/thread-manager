import identity.web
import utils.auth.authorization as authorization
from azure.monitor.opentelemetry import configure_azure_monitor  # noqa: F401
from flask import Flask, redirect, render_template, request, session, url_for
from flask_session import Session
from dotenv import load_dotenv
from datetime import datetime
from zoneinfo import ZoneInfo


import app_config
from social_media.poster import SocialMediaPoster
from utils.auth.auth_utils import check_auth
from content.blog_promo.blog_promo_blueprint import blog_promo_bp
from content.countdown.countdown_blueprint import countdown_bp
from content.fred.fred_blueprint import fred_bp  
from content.birds.birds_blueprint import birds_bp, upload_birds
from content.birds.bird_content import BirdContent
from dashboard.dashboard_blueprint import dashboard_bp, data_snapshot
from home_automation.visits.visits_blueprint import visits_bp
from home_automation.solar.solar_blueprint import solar_bp
from social_media.smp_blueprint import smp_bp, post_from_queue
from social_media.scheduler_blueprint import scheduler_bp, tickle_scheduler

from apscheduler.schedulers.background import BackgroundScheduler
from time import sleep

import logging
load_dotenv()

app = Flask(__name__)
app.config.from_object(app_config)
assert app.config["REDIRECT_PATH"] != "/", "REDIRECT_PATH must not be /"
Session(app)

app.auth = identity.web.Auth(
    session=session,
    authority=app.config["AUTHORITY"],
    client_id=app.config["CLIENT_ID"],
    client_credential=app.config["CLIENT_SECRET"],
)

# This section is needed for url_for("foo", _external=True) to automatically
# generate http scheme when this sample is running on localhost,
# and to generate https scheme when it is deployed behind reversed proxy.
# See also https://flask.palletsprojects.com/en/2.2.x/deploying/proxy_fix/
from werkzeug.middleware.proxy_fix import ProxyFix  # noqa: E402
logging.getLogger("werkzeug").setLevel(logging.WARNING)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

def require_auth():
    if not check_auth():
        if request.content_type == "application/x-www-form-urlencoded":
            return render_template("not_authorized.html")
        return "Unauthorized", 401

for bp in [fred_bp, birds_bp, blog_promo_bp, countdown_bp, dashboard_bp, visits_bp, smp_bp, scheduler_bp, solar_bp]:
    bp.before_request(require_auth)
    app.register_blueprint(bp)

if not app_config.RUNNING_LOCALLY:
    # running in Azure
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=post_from_queue, trigger="interval", minutes=5)
    scheduler.add_job(func=tickle_scheduler, trigger="interval", minutes=15)
    scheduler.add_job(func=upload_birds, trigger="interval", hours=2)
    scheduler.add_job(func=data_snapshot, trigger="interval", hours=12)
    scheduler.start()

@app.route("/login")
def login():
    return render_template(
        "login.html",
        version=identity.__version__,
        **app.auth.log_in(
            scopes=app_config.SCOPE,  # Have user consent to scopes during log-in
            redirect_uri=url_for(
                "auth_response", _external=True
            ),  # Optional. If present, this absolute URL must match your app's redirect_uri registered in Azure Portal
        ),
    )

@app.route(app_config.REDIRECT_PATH)
def auth_response():
    result = app.auth.complete_log_in(request.args)
    if "error" in result:
        return render_template("auth_error.html", result=result)
    return redirect(url_for("index"))

@app.route("/logout")
def logout():
    return redirect(app.auth.log_out(url_for("index", _external=True)))

@app.route("/")
def index():
    if not (app.config["CLIENT_ID"] and app.config["CLIENT_SECRET"]):
        # This check is not strictly necessary.
        # You can remove this check from your production code.
        return render_template("config_error.html")
    if not app.auth.get_user():
        return redirect(url_for("login"))

    b = BirdContent()
    latest_bird_update = b.get_latest_bird_update("America/Chicago")

    # convert to date and then format latest_bird_update as 'YYYY-MM-DD HH:MM AM/PM'
    latest_bird_update = datetime.fromisoformat(latest_bird_update).strftime("%Y-%m-%d %I:%M %p")

    
    return render_template(
        "index.html",
        user=app.auth.get_user(),
        api_token=app_config.API_TOKEN,
        version=identity.__version__,
        latest_bird_update = latest_bird_update,
    )

@app.template_filter('tzfilter')
def convert_timezone(value, timezone_str, picker=False):
    """
    Convert a datetime object from UTC to the specified timezone using zoneinfo.
    
    :param value: datetime object assumed to be in UTC (or naive)
    :param timezone_str: The target timezone string, e.g., 'America/Chicago'
    :return: datetime object in the target timezone
    """
    if not value:
        # set value for the current time in utc
        value = datetime.now(tz=ZoneInfo("UTC")).strftime("%Y-%m-%dT%H:%M")

        # return value.strftime("%Y-%m-%dT%H:%M")  # Format for <input type="datetime-local">

    value = datetime.fromisoformat(value)
    
    if not isinstance(value, datetime):
        raise ValueError("The value must be a datetime object")
    
    # If the datetime is naive, assume it's in UTC
    if value.tzinfo is None:
        value = value.replace(tzinfo=ZoneInfo("UTC"))
    
    # Convert the datetime to the target timezone
    try:
        target_tz = ZoneInfo(timezone_str)
    except Exception as e:
        raise ValueError(f"Invalid timezone: {timezone_str}") from e
    
    tzv = value.astimezone(target_tz)    
    
    if picker:
        return tzv.strftime("%Y-%m-%dT%H:%M")  # Format for <input type="datetime-local">
      
    # convert back to a string in the format 'YYYY-MM-DD HH:MM PM'
    return tzv.strftime("%Y-%m-%d %I:%M %p")