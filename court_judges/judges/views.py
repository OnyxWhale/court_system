from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.db.models import Exists, OuterRef, Value, BooleanField
from django.utils import timezone
from .models import Judge, WorkHistory

class JudgesListView(ListView):
    model = Judge
    template_name = "judges/judges_list.html"
    context_object_name = "judges"
    paginate_by = 21

    def get_queryset(self):
        current_date = timezone.now()
        active_history = WorkHistory.objects.filter(
            judge=OuterRef("pk"),
            start_date__lte=current_date,
            end_date__isnull=True
        )
        queryset = Judge.objects.annotate(
            is_working=Exists(active_history)
        ).order_by("-is_working", "full_name")

        return queryset

class JudgeDetailView(DetailView):
    model = Judge
    template_name = "judges/judge_detail.html"
    context_object_name = "judge"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["work_histories"] = self.object.workhistory_set.all()
        return context

class JudgeCreateView(CreateView):
    model = Judge
    template_name = "judges/judge_form.html"
    fields = ["full_name", "forum_account", "discord_id", "email", "telegram", "additional_info"]
    success_url = reverse_lazy("judges:judges_list")

class JudgeUpdateView(UpdateView):
    model = Judge
    template_name = "judges/judge_form.html"
    fields = ["full_name", "forum_account", "discord_id", "email", "telegram", "additional_info"]
    success_url = reverse_lazy("judges:judges_list")

class JudgeDeleteView(DeleteView):
    model = Judge
    template_name = "judges/judge_form.html"
    success_url = reverse_lazy("judges:judges_list")

class WorkHistoryCreateView(CreateView):
    model = WorkHistory
    template_name = "judges/work_history_form.html"
    fields = ["start_date", "end_date"]

    def form_valid(self, form):
        form.instance.judge = get_object_or_404(Judge, pk=self.kwargs["judge_pk"])
        
        # Проверка на пересечение промежутков
        new_start = form.instance.start_date
        new_end = form.instance.end_date
        existing_histories = WorkHistory.objects.filter(judge=form.instance.judge)

        for history in existing_histories:
            history_end = history.end_date if history.end_date else timezone.now()
            new_end_check = new_end if new_end else timezone.now()

            if (new_start <= history_end) and (history.start_date <= new_end_check):
                form.add_error(None, "Промежутки работы не должны пересекаться с существующими записями.")
                return self.form_invalid(form)

        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("judges:judge_detail", kwargs={"pk": self.kwargs["judge_pk"]})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["judge_pk"] = self.kwargs["judge_pk"]
        return context

class WorkHistoryUpdateView(UpdateView):
    model = WorkHistory
    template_name = "judges/work_history_form.html"
    fields = ["start_date", "end_date"]

    def form_valid(self, form):
        new_start = form.instance.start_date
        new_end = form.instance.end_date
        existing_histories = WorkHistory.objects.filter(judge=form.instance.judge).exclude(pk=form.instance.pk)

        for history in existing_histories:
            history_end = history.end_date if history.end_date else timezone.now()
            new_end_check = new_end if new_end else timezone.now()

            if (new_start <= history_end) and (history.start_date <= new_end_check):
                form.add_error(None, "Промежутки работы не должны пересекаться с существующими записями.")
                return self.form_invalid(form)

        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("judges:judge_detail", kwargs={"pk": self.object.judge.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["judge_pk"] = self.object.judge.pk
        return context

class WorkHistoryDeleteView(DeleteView):
    model = WorkHistory
    template_name = "judges/work_history_form.html"

    def get_success_url(self):
        return reverse_lazy("judges:judge_detail", kwargs={"pk": self.object.judge.pk})

def confirm_action(request):
    if request.method == "POST":
        password = request.POST.get("password")
        if password == settings.ACTION_CONFIRMATION_PASSWORD:
            return JsonResponse({"success": True})
        return JsonResponse({"success": False, "error": "Неверный пароль"})
    return JsonResponse({"success": False, "error": "Неверный метод запроса"})