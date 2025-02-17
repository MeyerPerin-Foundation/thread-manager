from flask import Blueprint, request, render_template, redirect, url_for, jsonify
from .solar_client import SolarClient
import logging

solar_bp = Blueprint("solar", __name__, url_prefix="/solar")

logger = logging.getLogger("tm-solar")

@solar_bp.route('/energy_sums', methods=['GET', 'POST'])
def energy_sums():
    if request.method == 'GET':
        # Just render the form
        return render_template('energy_sums.html')

    # POST -> process the form
    start_date_str = request.form['start_date']  # e.g. "2025-02-01"
    end_date_str = request.form['end_date']      # e.g. "2025-02-17"

    s = SolarClient()
    results = s.get_energy(start_date_str, end_date_str)

    # If you know exactly which fields you want, define them below:
    fields = [
        "ePvDay",
        "eExportDay",
        "eImportDay",
        "eConsumptionDay",
    ]

    # Initialize sums to 0 for each field
    sums = {field: 0.0 for field in fields}

    # Sum each document’s “e” field individually
    for doc in results:
        for field in fields:
            if field in doc and isinstance(doc[field], (int, float)):
                sums[field] += doc[field]

    # rename the keys in sums: ePVDay -> Solar Generation kWh, eExportDay -> Exported kWh, eImportDay -> Imported kWh, eConsumptionDay -> Consumption kWh
    sums = {
        "Solar Generation kWh": sums["ePvDay"],
        "Consumption kWh": sums["eConsumptionDay"],
        "Exported kWh": sums["eExportDay"],
        "Imported kWh": sums["eImportDay"],
    }
    
    # Pass these sums to the template
    return render_template('energy_sums.html', sums=sums, start_date=start_date_str, end_date=end_date_str)

