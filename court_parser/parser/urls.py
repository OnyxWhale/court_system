from django.urls import path
from .views import (
    ParserHomeView,
    ThreadListLink1View, ThreadDetailLink1View,
    ThreadListLink2View, ThreadDetailLink2View,
    ThreadListLink3View, ThreadDetailLink3View,
    parser_status
)

app_name = "parser"
urlpatterns = [
    path("", ParserHomeView.as_view(), name="home"),
    path("link1/threads/", ThreadListLink1View.as_view(), name="link1_threads"),
    path("link1/threads/<int:pk>/", ThreadDetailLink1View.as_view(), name="link1_thread_detail"),
    path("link2/threads/", ThreadListLink2View.as_view(), name="link2_threads"),
    path("link2/threads/<int:pk>/", ThreadDetailLink2View.as_view(), name="link2_thread_detail"),
    path("link3/threads/", ThreadListLink3View.as_view(), name="link3_threads"),
    path("link3/threads/<int:pk>/", ThreadDetailLink3View.as_view(), name="link3_thread_detail"),
    path("status/", parser_status, name="status"),
]