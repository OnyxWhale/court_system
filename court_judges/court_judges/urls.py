from django.urls import path, include

urlpatterns = [
    path("judges/", include("judges.urls", namespace="judges")),
]