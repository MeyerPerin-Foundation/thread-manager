import identity.web
import requests
from flask import Flask, redirect, render_template, request, session, url_for
from flask_session import Session
from azure.cosmos import CosmosClient, exceptions, PartitionKey

import app_config

__version__ = "0.7.0"  # The version of this sample, for troubleshooting purpose

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

app.jinja_env.globals.update(Auth=identity.web.Auth)  # Useful in template for B2C
auth = identity.web.Auth(
    session=session,
    authority=app.config["AUTHORITY"],
    client_id=app.config["CLIENT_ID"],
    client_credential=app.config["CLIENT_SECRET"],
)

def checkUserIsAuthorized(user) -> bool:
    if not user:
        return False
    sub = user.get("sub")
    # Connect to Cosmos DB
    client = CosmosClient(app_config.COSMOS_ENDPOINT, app_config.COSMOS_KEY)
    database = client.get_database_client(app_config.COSMOS_DATABASE)
    container = database.get_container_client("allowed_users")

    # Query to retrieve a specific record
    query = f"SELECT * FROM c WHERE c.id = 'sub'"

    # Fetching the record
    items = list(container.query_items(query=query, enable_cross_partition_query=True))

    if not items:
        print("No item found with the given ID")
    else:
        for item in items:
            print(item)



@app.route("/login")
def login():
    return render_template("login.html", version=__version__, **auth.log_in(
        scopes=app_config.SCOPE, # Have user consent to scopes during log-in
        redirect_uri=url_for("auth_response", _external=True), # Optional. If present, this absolute URL must match your app's redirect_uri registered in Azure Portal
        prompt="select_account",  # Optional. More values defined in  https://openid.net/specs/openid-connect-core-1_0.html#AuthRequest
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
    user = auth.get_user()
    if not user:
        return redirect(url_for("login"))
    # here there's a user, but we need to check if the user has permissions
    sub = user.get("sub")
    if (not sub) or (sub != app_config.AUTHORIZED_USER):
        return render_template('not_authorized.html', user=user, sub=sub)
    return render_template('index.html', user=user, version=__version__)


@app.route("/call_downstream_api")
def call_downstream_api():
    user = auth.get_user()
    if not user:
        return redirect(url_for("login"))
    # here there's a user, but we need to check if the user has permissions
    sub = user.get("sub")
    if (not sub) or (sub != app_config.AUTHORIZED_USER):
        return render_template('not_authorized.html', user=user, sub=sub
                               )

    token = auth.get_token_for_user(app_config.SCOPE)
    if "error" in token:
        return redirect(url_for("login"))
    # Use access token to call downstream api
    api_result = requests.get(
        app_config.ENDPOINT,
        headers={'Authorization': 'Bearer ' + token['access_token']},
        timeout=30,
    ).json()
    return render_template('display.html', result=api_result)


if __name__ == "__main__":
    app.run()
