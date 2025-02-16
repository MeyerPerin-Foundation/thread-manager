from flask import Blueprint, request, render_template, redirect, url_for, jsonify
from social_media import SocialMediaScheduler
import logging

logger = logging.getLogger("tm-scheduler")

scheduler_bp = Blueprint("scheduler", __name__, url_prefix="/scheduler")

@scheduler_bp.route("/", methods=["GET"])
def task_list():
    s = SocialMediaScheduler()
    tasks = s.list_tasks()
    return render_template("task_list.html", tasks=tasks)

@scheduler_bp.route("/<string:task_id>/edit", methods=["GET", "POST"])
def edit_task(task_id):
    s = SocialMediaScheduler()
    task = s.get_task(task_id)
    if request.method == "POST":
        task["command"] = request.form["command"]
        task["repeat_every"] = int(request.form["repeat_every"])
        task["repeat_unit"] = request.form["repeat_unit"]
        task["last_scheduled_time_utc"] = request.form["last_scheduled_time_utc"]
        task["next_scheduled_time_utc"] = request.form["next_scheduled_time_utc"]
        s.update_task(task_id, task)
        return redirect(url_for("scheduler.task_list"))
    return render_template("task_form.html", task=task)
    
@scheduler_bp.route("/<string:task_id>", methods=["GET"])
def view_task(task_id):
    s = SocialMediaScheduler()
    try:
        task = s.get_task(task_id)
        return render_template("task_detail.html", task=task)
    except:
        return "Task not found", 404

@scheduler_bp.route("/new", methods=["GET", "POST"])
def create_task():
    if request.method == "POST":
        task_data = {
            "id": request.form["id"],
            "command": request.form["command"],
            "repeat_every": int(request.form["repeat_every"]),
            "repeat_unit": request.form["repeat_unit"],
            "last_scheduled_time_utc": request.form["last_scheduled_time_utc"],
            "next_scheduled_time_utc": request.form["next_scheduled_time_utc"],
        }
        s = SocialMediaScheduler()
        s.create_task(task_data)
        return redirect(url_for("scheduler.task_list"))

    return render_template("task_form.html", task=None)    

@scheduler_bp.route("/<string:task_id>/delete", methods=["POST"])
def delete_task(task_id):
    s = SocialMediaScheduler()
    s.delete_task(task_id)
    return redirect(url_for("scheduler.task_list"))