import identity.web
from flask import Flask, redirect, render_template, request, session, url_for
from flask_session import Session
import authorization
import content_generator
import app_config
import birdbuddy_to_cosmos
import datetime

app = Flask(__name__)
app.config.from_object(app_config)
assert app.config["REDIRECT_PATH"] != "/", "REDIRECT_PATH must not be /"
Session(app)

# This section is needed for url_for("foo", _external=True) to automatically
# generate http scheme when this sample is running on localhost,
# and to generate https scheme when it is deployed behind reversed proxy.
# See also https://flask.palletsprojects.com/en/2.2.x/deploying/proxy_fix/
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

auth = identity.web.Auth(
    session=session,
    authority=app.config["AUTHORITY"],
    client_id=app.config["CLIENT_ID"],
    client_credential=app.config["CLIENT_SECRET"],
)

@app.route("/login")
def login():
    return render_template("login.html", version=identity.__version__, **auth.log_in(
        scopes=app_config.SCOPE, # Have user consent to scopes during log-in
        redirect_uri=url_for("auth_response", _external=True), # Optional. If present, this absolute URL must match your app's redirect_uri registered in Azure Portal
        ))

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
        return render_template('config_error.html')
    if not auth.get_user():
        return redirect(url_for("login"))
    return render_template('index.html', user=auth.get_user(), version=identity.__version__)

@app.route("/post_motd", methods=["POST"])
def post_motd():
    if not authorization.checkApiAuthorized(request.headers.get("Authorization")):
        return "Unauthorized", 401
    
    return content_generator.generate_and_post_motd()

@app.route("/post_midterms", methods=["POST"])
def post_midterms():
     if not authorization.checkApiAuthorized(request.headers.get("Authorization")):
        return "Unauthorized", 401
    
     return content_generator.generate_and_post_midterms_countdown()

@app.route("/post_ungovernable", methods=["POST"])
def post_ungovernable():
    if not authorization.checkApiAuthorized(request.headers.get("Authorization")):
        return "Unauthorized", 401
    
    return content_generator.generate_and_post_ungovernable()

@app.route("/post_too_far", methods=["POST"])
def post_too_far():
    if not authorization.checkApiAuthorized(request.headers.get("Authorization")):
        return "Unauthorized", 401
    
    return content_generator.generate_and_post_too_far()

@app.route("/post_bird_buddy", methods=["POST"])
def post_bird_buddy():
    if not authorization.checkApiAuthorized(request.headers.get("Authorization")):
        return "Unauthorized", 401
    
    return content_generator.generate_and_post_birdbuddy_picture()

@app.route("/update_birds", methods=["POST"])
async def update_birds():
    if not authorization.checkApiAuthorized(request.headers.get("Authorization")):
        return "Unauthorized", 401
    
    since = (datetime.datetime.now(datetime.UTC) - datetime.timedelta(hours=5))
  
    await birdbuddy_to_cosmos.update_birds(since)
    return "OK", 200


