import identity.web
import utils.auth.authorization as authorization

from azure.monitor.opentelemetry import configure_azure_monitor  # noqa: F401

from flask import Flask, redirect, render_template, request, session, url_for
from flask_session import Session

import app_config
import datetime
import dashboard.threads_data as threads_data
import dashboard.bluesky_data as bluesky_data
import content.blog_promo.sitemaps as sitemaps
import pytz
from dotenv import load_dotenv

from social_media.poster import SocialMediaPoster

from content.birds import BirdContent
from content.blog_promo import BlogPromoContent
from content.countdown import CountdownContent
from content.fred import FredContent
from content.ungovernable import UngovernableContent
from content.too_far import TooFarContent

#TODO: refactor
from utils.cosmosdb import BirdsDB, DashboardDB, VisitsDB, UngovernableDB, TooFarDB 
import content.birds.birdbuddy_to_cosmos as birdbuddy_to_cosmos

import logging
logging.basicConfig(level=logging.INFO)
logging.getLogger("azure").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

load_dotenv()

app = Flask(__name__)
app.config.from_object(app_config)
assert app.config["REDIRECT_PATH"] != "/", "REDIRECT_PATH must not be /"
Session(app)

# This section is needed for url_for("foo", _external=True) to automatically
# generate http scheme when this sample is running on localhost,
# and to generate https scheme when it is deployed behind reversed proxy.
# See also https://flask.palletsprojects.com/en/2.2.x/deploying/proxy_fix/
from werkzeug.middleware.proxy_fix import ProxyFix  # noqa: E402

logging.getLogger("werkzeug").setLevel(logging.WARNING)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)


auth = identity.web.Auth(
    session=session,
    authority=app.config["AUTHORITY"],
    client_id=app.config["CLIENT_ID"],
    client_credential=app.config["CLIENT_SECRET"],
)


def check_auth() -> bool:
    return authorization.checkUserIsAuthorized(
        auth.get_user()
    ) or authorization.checkApiAuthorized(request.headers.get("Authorization"))


@app.route("/login")
def login():
    return render_template(
        "login.html",
        version=identity.__version__,
        **auth.log_in(
            scopes=app_config.SCOPE,  # Have user consent to scopes during log-in
            redirect_uri=url_for(
                "auth_response", _external=True
            ),  # Optional. If present, this absolute URL must match your app's redirect_uri registered in Azure Portal
        ),
    )

@app.route(app_config.REDIRECT_PATH)
def auth_response():
    result = auth.complete_log_in(request.args)
    if "error" in result:
        return render_template("auth_error.html", result=result)
    return redirect(url_for("index"))

@app.route("/logout")
def logout():
    return redirect(auth.log_out(url_for("index", _external=True)))

@app.route("/")
def index():
    if not (app.config["CLIENT_ID"] and app.config["CLIENT_SECRET"]):
        # This check is not strictly necessary.
        # You can remove this check from your production code.
        return render_template("config_error.html")
    if not auth.get_user():
        return redirect(url_for("login"))
    return render_template(
        "index.html",
        user=auth.get_user(),
        api_token=app_config.API_TOKEN,
        version=identity.__version__,
    )

@app.route("/post_midterms", methods=["POST"])
def post_midterms():
    if not check_auth():
        if request.content_type == "application/x-www-form-urlencoded":
            return render_template("not_authorized.html")
        return "Unauthorized", 401

    c = CountdownContent()
    d = c.post_midterms_countdown()
    return d.result()

@app.route("/post_ungovernable", methods=["POST"])
def post_ungovernable():
    if not check_auth():
        if request.content_type == "application/x-www-form-urlencoded":
            return render_template("not_authorized.html")
        return "Unauthorized", 401

    u = UngovernableContent()
    d = u.post_ungovernable()
    return d.result()

@app.route("/post_too_far", methods=["POST"])
def post_too_far():
    if not check_auth():
        if request.content_type == "application/x-www-form-urlencoded":
            return render_template("not_authorized.html")
        return "Unauthorized", 401

    f = TooFarContent()
    d = f.post_too_far()
    return d.result()

@app.route("/post_bird_buddy", methods=["POST"])
def post_bird_buddy():
    if not check_auth():
        if request.content_type == "application/x-www-form-urlencoded":
            return render_template("not_authorized.html")
        return "Unauthorized", 401

    b = BirdContent()
    d = b.post_birdbuddy_picture()
    return d.result()

@app.route("/update_birds", methods=["POST"])
async def update_birds():
    if not check_auth():
        if request.content_type == "application/x-www-form-urlencoded":
            return render_template("not_authorized.html")
        return "Unauthorized", 401

    birds = BirdsDB()
    now = datetime.datetime.now(datetime.UTC).isoformat()
    last_update = birds.get_latest_bird_update()

    await birdbuddy_to_cosmos.update_birds(since=last_update)
    birds.set_latest_bird_update(now)
    return "OK", 200


@app.route("/dashboard", methods=["GET"])
def dashboard():
    if not check_auth():
        if request.content_type == "application/x-www-form-urlencoded":
            return render_template("not_authorized.html")
        return "Unauthorized", 401

    data_snapshot()

    dash = DashboardDB()
    dash_data = dash.latest_dashboard_data()

    return render_template("dashboard.html", data_payload=dash_data)


@app.route("/take_data_snapshot", methods=["POST"])
def data_snapshot():
    if not check_auth():
        if request.content_type == "application/x-www-form-urlencoded":
            return render_template("not_authorized.html")
        return "Unauthorized", 401

    payload = {}

    birds = BirdsDB()
    ungov = UngovernableDB()
    too_far = TooFarDB()
    dash = DashboardDB()

    # Combine the data into a single payload
    payload.update(birds.count_birds())
    payload.update(ungov.count_ungovernable())
    payload.update(too_far.count_too_far())
    payload.update({"threads_followers": threads_data.get_follower_count()})
    payload.update({"bluesky_followers": bluesky_data.get_follower_count()})

    dash.update_dashboard(payload)

    return "OK", 200


@app.route("/update_sitemap", methods=["POST"])
def update_sitemap():
    if not check_auth():
        if request.content_type == "application/x-www-form-urlencoded":
            return render_template("not_authorized.html")
        return "Unauthorized", 401

    # sitemap_url = request.json["sitemap_url"]
    sitemap_url = "https://meyerperin.org/sitemap.xml"
    sitemaps.process_sitemap(sitemap_url)

    return "OK", 200


@app.route("/post_blog_promo", methods=["POST"])
def post_blog_promo():
    if not check_auth():
        if request.content_type == "application/x-www-form-urlencoded":
            return render_template("not_authorized.html")
        return "Unauthorized", 401
    
    b = BlogPromoContent()
    return b.post_blog_promo()


@app.route("/update_dogtopia_visits", methods=["POST"])
def update_dogtopia_visits():
    if not check_auth():
        if request.content_type == "application/x-www-form-urlencoded":
            return render_template("not_authorized.html")
        return "Unauthorized", 401

    # get the data
    data = request.json

    if "date" not in data:
        # get the time in UTC and convert it to the CST timezone using the pytz library
        now = datetime.datetime.now(datetime.UTC)
        cst = pytz.timezone("America/Chicago")
        cst_now = now.astimezone(cst)
        data["date"] = cst_now.strftime("%Y-%m-%d")

    if "visits" not in data:
        visits = -1
    else:
        visits = data["visits"]

    visitsdb = VisitsDB()
    visitsdb.update_dogtopia_visits(data["date"], visits)

    return "OK", 200


@app.route("/insert_visit", methods=["POST"])
def insert_visit():
    app.logger.info("Called insert_visit")
    if not check_auth():
        if request.content_type == "application/x-www-form-urlencoded":
            return render_template("not_authorized.html")
        return "Unauthorized", 401

    data = request.json

    if "date" not in data:
        # get the time in UTC and convert it to the CST timezone using the pytz library
        now = datetime.datetime.now(datetime.UTC)
        cst = pytz.timezone("America/Chicago")
        cst_now = now.astimezone(cst)
        data["date"] = cst_now.strftime("%Y-%m-%d %H:%M:%S")

    if "location" not in data:
        app.logger.error(f"Missing location. Payload was {data}")
        return "Missing location", 400
    
    if "person" not in data:
        app.logger.error(f"Missing person. Payload was {data}")
        return "Missing person", 400

    visitsdb = VisitsDB()
    visitsdb.insert_visit(date=data["date"], location=data["location"], person=data["person"])

    return "OK", 200

@app.route("/bird_list", methods=["GET"])
def bird_list():
    if not check_auth():
        if request.content_type == "application/x-www-form-urlencoded":
            return render_template("not_authorized.html")
        return "Unauthorized", 401
    
    birds = BirdsDB()
    return render_template("bird_list.html", bird_list=birds.get_bird_list())


@app.route("/bird_details/<string:bird_id>", methods=["GET", "POST"])
def details(bird_id):
    if not check_auth():
        if request.content_type == "application/x-www-form-urlencoded":
            return render_template("not_authorized.html")
        return "Unauthorized", 401
    
    birds = BirdsDB()
    record = birds.get_bird(bird_id)
    if not record:
        return "Record not found", 404

    if request.method == 'POST':
        new_species = request.form.get('species')
        hidden_status = request.form.get('hidden') == 'true'

        if new_species:
            record['species'] = new_species
        record['hidden'] = hidden_status

        # Update the record in Cosmos DB
        try:
            birds.update_bird(record)
        except Exception as e:
            return f"Failed to update Cosmos DB: {e}", 500
        
        return render_template("bird_list.html", bird_list=birds.get_bird_list())

    return render_template('bird_details.html', record=record)

@app.route("/post_egg_prices", methods=["POST"])
def post_egg_prices():
    if not check_auth():
        if request.content_type == "application/x-www-form-urlencoded":
            return render_template("not_authorized.html")
        return "Unauthorized", 401

    fred = FredContent()
    d = fred.post_egg_prices()
    return d.result()


@app.route("/post_gas_prices", methods=["POST"])
def post_gas_prices():
    if not check_auth():
        if request.content_type == "application/x-www-form-urlencoded":
            return render_template("not_authorized.html")
        return "Unauthorized", 401

    fred = FredContent()
    d = fred.post_gas_prices()
    return d.result()


@app.route("/post_from_queue", methods=["POST"])
def post_from_queue():
    if not check_auth():
        if request.content_type == "application/x-www-form-urlencoded":
            return render_template("not_authorized.html")
        return "Unauthorized", 401

    poster = SocialMediaPoster()
    d = poster.post_next_document()
    return d.result()