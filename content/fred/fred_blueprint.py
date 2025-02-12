from flask import Blueprint, request, render_template
from content.fred import FredContent

fred_bp = Blueprint('fred', __name__, url_prefix='/fred')

@fred_bp.route("/post_egg_prices", methods=["POST"])
def post_egg_prices():
    fred = FredContent()
    d = fred.post_egg_prices()
    if d:
        return d.result()
    else:
        return "No content", 204


@fred_bp.route("/post_gas_prices", methods=["POST"])
def post_gas_prices():
    fred = FredContent()
    d = fred.post_gas_prices()
    if d:
        return d.result()
    else:
        return "No content", 204