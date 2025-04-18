from django.urls import path
from .views import StatsListView

app_name = "stats"

urlpatterns = [
    path("", StatsListView.as_view(), name="stats_list"),
]