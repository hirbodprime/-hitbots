# tetris/urls.py
from django.urls import path
from . import views

app_name = "tetris"

urlpatterns = [
    path("", views.tetris_page, name="play"),
    path("submit-score/", views.submit_score, name="submit_score"),
]
