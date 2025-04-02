from django.urls import path
from .views import ParserHomeView, ThreadListView, ThreadDetailView
from . import views

app_name = "parser"
urlpatterns = [
    path("", ParserHomeView.as_view(), name="home"),
    path("threads/", ThreadListView.as_view(), name="threads"),
    path("threads/<int:pk>/", ThreadDetailView.as_view(), name="thread_detail"),
    path("status/", views.parser_status, name="status"),
]