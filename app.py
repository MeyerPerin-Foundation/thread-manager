import identity.web
from flask import Flask, redirect, render_template, request, session, url_for
from flask_session import Session
import authorization
import content_generator
import app_config
import birdbuddy_to_cosmos
import datetime
from cosmosdb import _dbutils, Birds, Dashboard, TooFar, Ungovernable, Visits
import threads_data
import bluesky_data
import sitemaps
import pytz
from azure.monitor.opentelemetry import configure_azure_monitor  # noqa: F401
from dotenv import load_dotenv
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


@app.route("/lucas_test", methods=["POST"])
def lucas_test():
    if not check_auth():
        if request.content_type == "application/x-www-form-urlencoded":
            return render_template("not_authorized.html")
        return "Unauthorized", 401

    data = {}
    if request.content_type == "application/x-www-form-urlencoded":
        data["content_type"] = "form"
        data["form"] = request.form
    else:
        data["content_type"] = "json"
        data["json"] = request.json

    _dbutils._insert_test_record(data)
    return "OK", 200


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


@app.route("/post_motd", methods=["POST"])
def post_motd():
    if not check_auth():
        if request.content_type == "application/x-www-form-urlencoded":
            return render_template("not_authorized.html")
        return "Unauthorized", 401

    return content_generator.generate_and_post_motd()


@app.route("/post_midterms", methods=["POST"])
def post_midterms():
    if not check_auth():
        if request.content_type == "application/x-www-form-urlencoded":
            return render_template("not_authorized.html")
        return "Unauthorized", 401

    return content_generator.generate_and_post_midterms_countdown()


@app.route("/post_severance", methods=["POST"])
def post_severance():
    if not check_auth():
        if request.content_type == "application/x-www-form-urlencoded":
            return render_template("not_authorized.html")
        return "Unauthorized", 401

    return content_generator.generate_and_post_severance_s2_countdown()


@app.route("/post_ungovernable", methods=["POST"])
def post_ungovernable():
    if not check_auth():
        if request.content_type == "application/x-www-form-urlencoded":
            return render_template("not_authorized.html")
        return "Unauthorized", 401

    return content_generator.generate_and_post_ungovernable()


@app.route("/post_too_far", methods=["POST"])
def post_too_far():
    if not check_auth():
        if request.content_type == "application/x-www-form-urlencoded":
            return render_template("not_authorized.html")
        return "Unauthorized", 401

    return content_generator.generate_and_post_too_far()


@app.route("/post_bird_buddy", methods=["POST"])
def post_bird_buddy():
    if not check_auth():
        if request.content_type == "application/x-www-form-urlencoded":
            return render_template("not_authorized.html")
        return "Unauthorized", 401

    return content_generator.generate_and_post_birdbuddy_picture()


@app.route("/update_birds", methods=["POST"])
async def update_birds():
    if not check_auth():
        if request.content_type == "application/x-www-form-urlencoded":
            return render_template("not_authorized.html")
        return "Unauthorized", 401

    birds = Birds()
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

    dash = Dashboard()
    dash_data = dash.latest_dashboard_data()

    return render_template("dashboard.html", data_payload=dash_data)


@app.route("/take_data_snapshot", methods=["POST"])
def data_snapshot():
    if not check_auth():
        if request.content_type == "application/x-www-form-urlencoded":
            return render_template("not_authorized.html")
        return "Unauthorized", 401

    payload = {}

    birds = Birds()
    ungov = Ungovernable()
    too_far = TooFar()
    dash = Dashboard()
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

    return content_generator.generate_and_post_blog_promo()


@app.route("/post_bsky_reminder", methods=["POST"])
def post_bsky_reminder():
    if not check_auth():
        if request.content_type == "application/x-www-form-urlencoded":
            return render_template("not_authorized.html")
        return "Unauthorized", 401

    return content_generator.generate_and_post_bsky_reminder()


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

    visitsdb = Visits()
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

    visitsdb = Visits()
    visitsdb.insert_visit(date=data["date"], location=data["location"], person=data["person"])

    return "OK", 200

@app.route("/bird_list", methods=["GET"])
def bird_list():
    if not check_auth():
        if request.content_type == "application/x-www-form-urlencoded":
            return render_template("not_authorized.html")
        return "Unauthorized", 401
    
    birds = Birds()
    return render_template("bird_list.html", bird_list=birds.get_bird_list())


@app.route("/bird_details/<string:bird_id>", methods=["GET", "POST"])
def details(bird_id):
    if not check_auth():
        if request.content_type == "application/x-www-form-urlencoded":
            return render_template("not_authorized.html")
        return "Unauthorized", 401
    
    birds = Birds()
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
