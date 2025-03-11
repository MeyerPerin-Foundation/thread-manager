from flask import Blueprint, request, render_template, redirect, url_for, jsonify
from .solar_client import SolarClient
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import app_config

solar_bp = Blueprint("solar", __name__, url_prefix="/solar")

logger = logging.getLogger("tm-solar")

@solar_bp.route('/energy_sums', methods=['GET', 'POST'])
def energy_sums():

    today = datetime.now(ZoneInfo(app_config.LOCAL_TIME_ZONE))  # Get current date in the specified timezone

    # Last day of this month’s 1st - 1 day = last day of last month
    first_day_of_this_month = today.replace(day=1)
    last_day_of_prev_month = first_day_of_this_month - timedelta(days=1)

    default_start = last_day_of_prev_month.strftime('%Y-%m-%d')
    default_end = today.strftime('%Y-%m-%d')

    if request.method == 'GET':
        return render_template(
            'energy_sums.html',
            default_start=default_start,
            default_end=default_end
        )

    # POST -> process the form
    start_date_str = request.form['start_date']  # e.g. "2025-02-01"
    end_date_str = request.form['end_date']      # e.g. "2025-02-17"

    s = SolarClient()
    query_results = s.get_energy(start_date_str, end_date_str)

    fields = [
        "ePvDay",
        "eExportDay",
        "eImportDay",
        "eConsumptionDay",
    ]


    fields_map = {
        "Solar Generation": "ePvDay",
        "Consumption": "eConsumptionDay",
        "Exported": "eExportDay",
        "Imported": "eImportDay"
    }

    sums = {label: 0.0 for label in fields_map}

    num_days = len(query_results)

    for doc in query_results:
        for label, field_name in fields_map.items():
            val = doc.get(field_name, 0)
            if isinstance(val, (int, float)):
                sums[label] += val        

    net_generation = sums["Solar Generation"] - sums["Consumption"]
    net_exports = sums["Exported"] - sums["Imported"]

    sums["Net Generation"] = net_generation
    sums["Net Exports"] = net_exports

    field_data = {}
    for label, total_sum in sums.items():
        daily_avg = round(total_sum / num_days, 1)
        field_data[label] = {
            "sum": round(total_sum, 1),
            "avg": daily_avg
        }

    results = {
        "num_days": num_days,
        "field_data": field_data
    }

    return render_template(
        'energy_sums.html', 
        results=results, 
        start_date=start_date_str, 
        end_date=end_date_str,
        default_start=start_date_str,
        default_end=end_date_str        
    )


