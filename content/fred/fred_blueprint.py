from flask import Blueprint, request, render_template
from content.fred import FredContent

fred_bp = Blueprint('fred', __name__, url_prefix='/fred')

@fred_bp.route("/queue_chart", methods=["POST"])
def queue_chart():

    fred = FredContent()
    data = request.get_json()
    id = fred.queue_time_series_plot(
        series_id = data["series_id"],
        series_description = data["series_description"],
        series_highlight = data.get("series_highlight", "max"),
        start_date = data.get("start_date",  "2024-01-01"),
        end_date = data.get("end_date"),
        hashtags = data.get("hashtags"),
        after_utc = data.get("after_utc"),
    )
    if not id:
        return "No content", 204
    
    return {"id": id}, 202
    