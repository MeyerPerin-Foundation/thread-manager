from flask import Blueprint, request, render_template
from content.birds import BirdContent
from .birds_db import BirdsDB
import datetime

birds_bp = Blueprint('birds', __name__, url_prefix='/birds')

@birds_bp.route("/post_bird_buddy", methods=["POST"])
def post_bird_buddy():

    b = BirdContent()

    # if there's any json data in the request, get its after_utc
    after_utc = request.json.get("after_utc", None)    

    if after_utc:
        b.generate_birdbuddy_post(after_utc=after_utc)
        return "Accepted", 202        

    d = b.post_birdbuddy_picture()
    if d:
        return d.result()
    else:
        return "No content", 204

@birds_bp.route("/upload_birds", methods=["POST"])
async def upload_birds():

    birds = BirdContent()
    now = datetime.datetime.now(datetime.UTC).isoformat()
    last_update = birds.get_latest_bird_update()

    await birds.upload_birds(since=last_update)
    birds.set_latest_bird_update(now)
    return "OK", 200

@birds_bp.route("/list", methods=["GET"])
def bird_list():
    
    birds = BirdsDB()
    return render_template("bird_list.html", bird_list=birds.get_bird_list())
    
@birds_bp.route("/bird_details/<string:bird_id>", methods=["GET", "POST"])
def details(bird_id):
    
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
