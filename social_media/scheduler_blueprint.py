from flask import Blueprint, request, render_template, redirect, url_for, jsonify
from social_media import SocialMediaScheduler
import logging

logger = logging.getLogger("tm-scheduler")

scheduler_bp = Blueprint("scheduler", __name__, url_prefix="/scheduler")

@scheduler_bp.route("/tickle_scheduler", methods=["POST"])
def tickle_scheduler():

    scheduler = SocialMediaScheduler()
    
    schedule_items = scheduler.list_expired_schedules()
    ids = []
    for schedule in schedule_items:
        id = scheduler.generate_post_document(schedule)
        scheduler.update_schedule(schedule)
        if id:
            ids.append(id)

    if len(ids) > 0:
        return f"Accepted with ids: {ids}", 202
    else:
        return "No content", 204

@scheduler_bp.route("/", methods=["GET"])
def task_list():
    s = SocialMediaScheduler()
    tasks = s.list_tasks()
    return render_template("task_list.html", tasks=tasks)

@scheduler_bp.route("/<string:task_id>/edit", methods=["GET", "POST"])
def edit_task(task_id):
    s = SocialMediaScheduler()
    # flatten request.form to a dict
    logger.debug(f"Received task: {request.form}")
    task_data = s.get_task(task_id)
    if request.method == "POST":
        task_data["command"] = request.form["command"]
        task_data["repeat_every"] = int(request.form["repeat_every"])
        task_data["repeat_unit"] = request.form["repeat_unit"]
        task_data["last_scheduled_time_utc"] = request.form["last_scheduled_time_utc"]
        task_data["next_scheduled_time_utc"] = request.form["next_scheduled_time_utc"]
        # for each key in request.form, if the key starts with "command_parameters.", add it to task_data
        for key in request.form:
            if key.startswith("command_parameters_"):
                # if there's no command_parameters key in task_data, create it
                if "command_parameters" not in task_data:
                    task_data["command_parameters"] = {}
                task_data["command_parameters"][key[len("command_parameters_"):]] = request.form[key] 
        logger.debug(f"Updating task {task_id}: {task_data}")
        s.update_task(task_id, task_data)
        return redirect(url_for("scheduler.task_list"))
    return render_template("task_form.html", task=task_data)
    
@scheduler_bp.route("/<string:task_id>", methods=["GET"])
def view_task(task_id):
    s = SocialMediaScheduler()
    try:
        task_data = s.get_task(task_id)
        return render_template("task_detail.html", task=task_data)
    except:
        return "Task not found", 404

@scheduler_bp.route("/new", methods=["GET", "POST"])
def create_task():
    if request.method == "POST":
        request.form = request.form.to_dict(flat=True)
        logger.debug(f"Received task: {request.form}")
        task_data = {
            "id": request.form["id"],
            "command": request.form["command"],
            "repeat_every": int(request.form["repeat_every"]),
            "repeat_unit": request.form["repeat_unit"],
            "last_scheduled_time_utc": request.form["last_scheduled_time_utc"],
            "next_scheduled_time_utc": request.form["next_scheduled_time_utc"],
        }
        for key in request.form:
            if key.startswith("command_parameters_"):
                # if there's no command_parameters key in task_data, create it
                if "command_parameters" not in task_data:
                    task_data["command_parameters"] = {}
                task_data["command_parameters"][key[len("command_parameters_"):]] = request.form[key] 
        s = SocialMediaScheduler()
        logger.debug(f"Creating task: {task_data}")
        s.create_task(task_data)
        return redirect(url_for("scheduler.task_list"))

    return render_template("task_form.html", task=None)    

@scheduler_bp.route("/<string:task_id>/delete", methods=["POST"])
def delete_task(task_id):
    s = SocialMediaScheduler()
    s.delete_task(task_id)
    return redirect(url_for("scheduler.task_list"))

