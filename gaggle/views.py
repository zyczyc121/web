from django.shortcuts import render
from competition.models import Competition
from course.models import Course
from competition.util import active_user_count
from django.contrib import messages


def index(request):
    active_competitions = Competition.objects.all().order_by("-start_datetime")
    active_users = request.session.get('active_users', active_user_count())
    active_courses = Course.objects.all().order_by("-start_datetime")

    return render(request, "index.html", {
        "active_competitions": active_competitions,
        "active_courses": active_courses,
        "active_users": active_users,
    })

def privacy(request):
    active_users = request.session.get('active_users', active_user_count())

    return render(request, "privacy.html", {
        "active_users": active_users,
    })

def terms(request):
    active_users = request.session.get('active_users', active_user_count())

    return render(request, "terms.html", {
        "active_users": active_users,
    })

def contact(request):
    active_users = request.session.get('active_users', active_user_count())

    return render(request, "contact.html", {
        "active_users": active_users,
    })

def about(request):
    active_users = request.session.get('active_users', active_user_count())

    return render(request, "about.html", {
        "active_users": active_users,
    })
