from django.urls import path
from .views import (
    JudgesListView, JudgeDetailView, JudgeCreateView, JudgeUpdateView, JudgeDeleteView,
    WorkHistoryCreateView, WorkHistoryUpdateView, WorkHistoryDeleteView, confirm_action
)

app_name = "judges"
urlpatterns = [
    path("", JudgesListView.as_view(), name="judges_list"),
    path("<int:pk>/", JudgeDetailView.as_view(), name="judge_detail"),
    path("create/", JudgeCreateView.as_view(), name="judge_create"),
    path("<int:pk>/update/", JudgeUpdateView.as_view(), name="judge_update"),
    path("<int:pk>/delete/", JudgeDeleteView.as_view(), name="judge_delete"),
    path("<int:judge_pk>/history/create/", WorkHistoryCreateView.as_view(), name="work_history_create"),
    path("history/<int:pk>/update/", WorkHistoryUpdateView.as_view(), name="work_history_update"),
    path("history/<int:pk>/delete/", WorkHistoryDeleteView.as_view(), name="work_history_delete"),
    path("confirm-action/", confirm_action, name="confirm_action"),
]