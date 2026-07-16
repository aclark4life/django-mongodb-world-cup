from django.urls import path

from . import views

urlpatterns = [
    path("goals/total/", views.tournament_goals, name="tournament_goals"),
    path("goals/top-scorers/", views.top_scorers, name="top_scorers"),
    path("shell/", views.query_shell, name="query_shell"),
]