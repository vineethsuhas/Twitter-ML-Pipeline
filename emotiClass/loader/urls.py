from django.conf.urls import *

from . import views

urlpatterns = [
    url(r'offline-loader/', views.offline_loader_view),
    url(r'twitter-tracks/', views.twitter_tracks_view),
    url(r'project-upload/', views.project_upload_view),
]