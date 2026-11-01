from django.urls import path

from . import views

urlpatterns = [
    path("", views.upload_list, name="upload_list"),
    path("new/", views.manual_feedback, name="manual_feedback"),
    path("upload/", views.csv_upload, name="csv_upload"),
    path("<int:pk>/", views.upload_detail, name="upload_detail"),
    path("<int:pk>/delete/", views.upload_delete, name="upload_delete"),
]