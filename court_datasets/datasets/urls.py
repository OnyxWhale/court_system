from django.urls import path
from . import views
from django.shortcuts import redirect

app_name = "datasets"

urlpatterns = [
    path("", lambda request: redirect("datasets:federal_court_list"), name="datasets_list"),
    path("supreme/", views.SupremeCourtListView.as_view(), name="supreme_court_list"),
    path("federal/", views.FederalCourtListView.as_view(), name="federal_court_list"),
    path("rehabilitation/", views.RehabilitationListView.as_view(), name="rehabilitation_list"),
    path("update_note/", views.update_note, name="update_note"),
]