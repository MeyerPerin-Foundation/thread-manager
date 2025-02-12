from flask import Blueprint, request
from .visits_db import VisitsDB

import datetime
import pytz

visits_bp = Blueprint('visits', __name__, url_prefix='/visits')

@visits_bp.route("/update_dogtopia_visits", methods=["POST"])
def update_dogtopia_visits():
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


@visits_bp.route("/insert_visit", methods=["POST"])
def insert_visit():

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