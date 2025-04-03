from django.urls import path
from .views import DatasetsListView, update_note
from . import views

app_name = "datasets"
urlpatterns = [
    path("", DatasetsListView.as_view(), name="datasets_list"),
    path("update-note/", update_note, name="update_note"),
]