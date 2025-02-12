from flask import Blueprint, request, render_template
from content.birds import BirdContent
from utils.cosmosdb.birds import BirdsDB

birds_bp = Blueprint('birds', __name__, url_prefix='/birds')

@birds_bp.route("/post_bird_buddy", methods=["POST"])
def post_bird_buddy():

    b = BirdContent()
    d = b.post_birdbuddy_picture()
    if d:
        return d.result()
    else:
        return "No content", 204

@birds_bp.route("/update_birds", methods=["POST"])
async def update_birds():

    birds = BirdsDB()
    now = datetime.datetime.now(datetime.UTC).isoformat()
    last_update = birds.get_latest_bird_update()

    await birdbuddy_to_cosmos.update_birds(since=last_update)
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
