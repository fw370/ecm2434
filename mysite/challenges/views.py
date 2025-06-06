import json
from typing import Iterable
import datetime

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpRequest
from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import JsonResponse

from db.models import Task, Location, CompleteTask


def completed_challenge(request: HttpRequest) -> None:
    coords = [request.POST["lat"], request.POST["lng"]]
    for i, coord in enumerate(coords):
        if coord == "":
            coords[i] = None

    print(request.FILES['image'].read())

    CompleteTask(
        user=request.user, 
        task=Task.objects.get(id=request.POST["task_id"]), 
        image=request.FILES['image'],
        latitude=coords[0],
        longtitude=coords[1],
        completion_date=datetime.datetime.now()
    ).save(check_duplicate=True)

@login_required(login_url="/login")
def render_map(request: HttpRequest, tasks: Iterable[Task]=Task.objects.all()):
    if request.method == "POST":
        try:
            completed_challenge(request)
        except ValidationError as e:
            return JsonResponse({'message':str(e)}, status=400)

    # Organising data into formats for front-end rendering
    loc_tasks = {}
    positions = []
    for task in tasks:
        # Tasks with no location
        if task.location is None:
            task.location = Location()
            task.location.locationName = "Extras"
            task.location.longtitude = None
            task.location.latitude = None

        # Group tasks by their location, data for sidebar showing active tasks
        if str(task.location) not in loc_tasks:
            loc_tasks[str(task.location)] = []
        loc_tasks[str(task.location)].append(task)

        # Data for rendering map in js
        positions.append(
            {
                "lat": task.location.latitude,
                "lng": task.location.longtitude,
                "location_name": str(task.location)
            }
        )

    # Put extras (tasks with no location) at the bottom of all the locations
    if loc_tasks.get("Extras"):
        loc_tasks["Extras"] = loc_tasks.pop("Extras")

    context = {
        "API_KEY": settings.MAPS_API_KEY,
        "tasks": loc_tasks,
        "positions": json.dumps(positions),
        "center": json.dumps(settings.MAPS_CENTER_COORDINATES),
        "timeout_millis": settings.MAPS_TIMEOUTMILLIS
    }
    return render(request, "challenges/map.html", context=context)
