from django.views.generic import ListView
from django.http import JsonResponse
from .models import ForumThread, ClaimNote
from .utils import get_claim_data
from django.db import connections
from django.db.utils import OperationalError
from .tasks import update_claims_data
from django.db.models.functions import Length

class DatasetsListView(ListView):
    model = ForumThread
    template_name = "datasets/datasets_list.html"
    context_object_name = "claims"
    paginate_by = 100

    def get_queryset(self):
        try:
            connections["parser_db"].ensure_connection()
            queryset = ForumThread.objects.using("parser_db").prefetch_related("threadmessage_set").order_by("-created_at")
            # Фильтр на длину заголовка (> 5 символов) с использованием Length
            queryset = queryset.annotate(title_length=Length("title")).filter(title_length__gt=5)

            # Применение фильтров из GET-параметров
            title_filter = self.request.GET.get("title", "").strip()
            date_from = self.request.GET.get("date_from")
            date_to = self.request.GET.get("date_to")
            prefix_filter = self.request.GET.get("prefix")
            judge_filter = self.request.GET.get("judge", "").strip()
            note_filter = self.request.GET.get("note")
            urgent_filter = self.request.GET.get("urgent")

            if title_filter:
                queryset = queryset.filter(title__icontains=title_filter)
            if date_from:
                queryset = queryset.filter(created_at__gte=date_from)
            if date_to:
                queryset = queryset.filter(created_at__lte=date_to)
            if prefix_filter:
                queryset = queryset.filter(prefix=prefix_filter)
            if note_filter == "with":
                queryset = queryset.filter(claimnote__note__isnull=False)
            elif note_filter == "without":
                queryset = queryset.filter(claimnote__note__isnull=True)

            return queryset
        except OperationalError as e:
            print(f"Ошибка подключения к parser_db: {e}")
            return ForumThread.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        claims_data = []

        # Обработка queryset для добавления вычисляемых данных
        for thread in context["object_list"]:
            claim_data = get_claim_data(thread)
            note = ClaimNote.objects.filter(thread_id=thread.id).first()
            claim_data["note"] = note.note if note else ""
            claim_data["thread_id"] = thread.id
            claims_data.append(claim_data)

        # Дополнительные фильтры, которые нельзя применить к queryset напрямую
        judge_filter = self.request.GET.get("judge", "").strip()
        urgent_filter = self.request.GET.get("urgent")
        if judge_filter or urgent_filter == "true":
            filtered_claims = []
            for claim in claims_data:
                if judge_filter and judge_filter.lower() not in claim["leading_judges"].lower():
                    continue
                if urgent_filter == "true":
                    first_response_time = self.parse_time_string(claim["first_response_time"])
                    court_time = self.parse_time_string(claim["court_time"])
                    if not (
                        (court_time > timedelta(days=7) and claim["prefix"] in ["На рассмотрении", "Нет"]) or
                        (claim["leading_judges"] == "Не определён" and claim["prefix"] == "Нет" and first_response_time > timedelta(days=2, hours=12))
                    ):
                        continue
                filtered_claims.append(claim)
            context["claims"] = filtered_claims
        else:
            context["claims"] = claims_data

        # Обновление кэша асинхронно
        update_claims_data.delay()

        # Уникальные судьи
        judges = sorted(set(claim["leading_judges"] for claim in claims_data if claim["leading_judges"]))
        context["judges"] = judges

        # Фильтры для шаблона
        context["filters"] = {
            "title": self.request.GET.get("title", ""),
            "date_from": self.request.GET.get("date_from"),
            "date_to": self.request.GET.get("date_to"),
            "prefix": self.request.GET.get("prefix"),
            "judge": judge_filter,
            "note": self.request.GET.get("note"),
            "urgent": urgent_filter,
        }
        return context

    def parse_time_string(self, time_str):
        if not time_str or time_str == "Нет данных" or time_str == "—":
            return timedelta(days=0)
        try:
            parts = time_str.split()
            days = int(parts[0]) if parts[0].isdigit() else 0
            hours = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0
            minutes = int(parts[4]) if len(parts) > 4 and parts[4].isdigit() else 0
            return timedelta(days=days, hours=hours, minutes=minutes)
        except (ValueError, IndexError):
            return timedelta(days=0)

def update_note(request):
    if request.method == "POST":
        thread_id = request.POST.get("thread_id")
        note_text = request.POST.get("note").strip()
        try:
            if note_text:
                note, _ = ClaimNote.objects.update_or_create(thread_id=thread_id, defaults={"note": note_text})
            else:
                ClaimNote.objects.filter(thread_id=thread_id).delete()
            return JsonResponse({"success": True})
        except Exception as e:
            print(f"Error in update_note: {e}")
            return JsonResponse({"success": False, "error": str(e)})
    return JsonResponse({"success": False, "error": "Invalid request"})