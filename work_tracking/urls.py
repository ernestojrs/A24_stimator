from django.urls import path
from . import views

urlpatterns = [

    path("", views.work_tracking_dashboard_view, name="work_tracking_dashboard"),
    path("my-schedule/", views.my_schedule_view, name="my_schedule"),
    path("assignments/new/", views.create_assignment_view, name="create_assignment"),
    path("assignments/", views.assignment_list_view, name="assignment_list"),
    path(
        "assignments/<int:assignment_id>/cancel/",
        views.cancel_assignment_view,
        name="cancel_assignment",
    ),
    path("calendar/", views.assignment_calendar_view, name="assignment_calendar"),

    path(
    "assignments/<int:assignment_id>/",
    views.assignment_detail_view,
    name="assignment_detail",
    ),

    path("profiles/", views.worker_directory_view, name="worker_directory"),

    path(
    "profiles/<int:profile_id>/",
    views.worker_profile_detail_view,
    name="worker_profile_detail",
    ),

    path(
    "assignments/<int:assignment_id>/edit/",
    views.edit_assignment_view,
    name="edit_assignment",
    ),

    path(
    "assignments/<int:assignment_id>/complete/",
    views.complete_assignment_view,
    name="complete_assignment",
    ),

    path("today/", views.todays_assignments_view, name="todays_assignments"),
    path("completed/", views.completed_assignments_view, name="completed_assignments"),
    path("cancelled/", views.cancelled_assignments_view, name="cancelled_assignments"),
    path("active/", views.active_assignments_view, name="active_assignments"),
    path("availability/", views.worker_availability_view, name="worker_availability"),
    path("assignments/export/csv/", views.export_assignments_csv_view, name="export_assignments_csv"),

    

]