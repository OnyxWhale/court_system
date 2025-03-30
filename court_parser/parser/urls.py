from django.urls import path
from .views import ParserHomeView, ThreadListView

app_name = "parser"
urlpatterns = [
    path("", ParserHomeView.as_view(), name="home"),
    path("threads/", ThreadListView.as_view(), name="threads"),
]