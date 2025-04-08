from django.views.generic import ListView
from django.http import JsonResponse, HttpResponseServerError
from .models import ForumThread, ClaimNote
from .utils import get_claim_data
from django.db import connections
from django.db.utils import OperationalError
from .tasks import update_claims_data
from django.core.cache import cache
from celery.exceptions import OperationalError as CeleryOperationalError
from datetime import datetime, timedelta

class DatasetsListView(ListView):
    model = ForumThread
    template_name = "datasets/datasets_list.html"
    context_object_name = "claims"
    paginate_by = 100

    def get_queryset(self):
        try:
            connections["parser_db"].ensure_connection()
            return ForumThread.objects.using("parser_db").prefetch_related("threadmessage_set").order_by("-created_at")
        except OperationalError as e:
            print(f"Ошибка подключения к parser_db: {e}")
            return ForumThread.objects.none()

    def parse_time_string(self, time_str):
        """Парсит строку времени (например, '2 д. 10 ч. 15 м.') в timedelta."""
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        claims_data = cache.get("claims_data")
        if not claims_data:
            print("Кэш пуст, загружаем данные напрямую.")
            claims_data = []
            try:
                for thread in self.get_queryset():
                    # Пропускаем темы с заголовком длиной 5 символов и меньше
                    if len(thread.title) <= 5:
                        continue
                    claim_data = get_claim_data(thread)
                    note = ClaimNote.objects.filter(thread_id=thread.id).first()
                    claim_data["note"] = note.note if note else ""
                    claim_data["thread_id"] = thread.id
                    claims_data.append(claim_data)
                cache.set("claims_data", claims_data, timeout=3600)
            except Exception as e:
                print(f"Ошибка при загрузке данных: {e}")
                claims_data = []
            try:
                update_claims_data.delay()
                print("Задача на обновление кэша отправлена в Celery.")
            except CeleryOperationalError as e:
                print(f"Ошибка Celery: {e}")

        # Фильтрация данных из кэша: исключаем темы с заголовком ≤ 5 символов
        filtered_claims_data = [claim for claim in claims_data if len(claim["title"]) > 5]

        # Получение фильтров из GET-параметров
        title_filter = self.request.GET.get("title", "").strip()
        date_from = self.request.GET.get("date_from")
        date_to = self.request.GET.get("date_to")
        prefix_filter = self.request.GET.get("prefix")
        judge_filter = self.request.GET.get("judge", "").strip()
        note_filter = self.request.GET.get("note")
        urgent_filter = self.request.GET.get("urgent")

        # Фильтрация данных
        filtered_data = filtered_claims_data
        if title_filter:
            filtered_data = [claim for claim in filtered_data if title_filter.lower() in claim["title"].lower()]
        if date_from:
            try:
                date_from_dt = datetime.strptime(date_from, "%Y-%m-%d")
                filtered_data = [claim for claim in filtered_data if claim["created_at"].replace(tzinfo=None) >= date_from_dt]
            except ValueError:
                pass
        if date_to:
            try:
                date_to_dt = datetime.strptime(date_to, "%Y-%m-%d")
                filtered_data = [claim for claim in filtered_data if claim["created_at"].replace(tzinfo=None) <= date_to_dt]
            except ValueError:
                pass
        if prefix_filter:
            filtered_data = [claim for claim in filtered_data if claim["prefix"] == prefix_filter]
        if judge_filter:
            filtered_data = [claim for claim in filtered_data if judge_filter.lower() in claim["leading_judges"].lower()]
        if note_filter == "with":
            filtered_data = [claim for claim in filtered_data if claim["note"]]
        elif note_filter == "without":
            filtered_data = [claim for claim in filtered_data if not claim["note"]]
        if urgent_filter == "true":
            filtered_data = [
                claim for claim in filtered_data
                if (
                    (claim["court_time"] and self.parse_court_time(claim["court_time"]) > timedelta(days=7) and
                     claim["prefix"] in ["На рассмотрении", "Нет"])
                ) or (
                    claim["leading_judges"] == "Не определён" and
                    claim["prefix"] == "Нет" and
                    claim["first_response_time"] != "Нет данных" and
                    self.parse_time_string(claim["first_response_time"]) > timedelta(days=2, hours=12)
                )
            ]

        # Получение уникальных судей
        judges = sorted(set(claim["leading_judges"] for claim in filtered_claims_data if claim["leading_judges"]))

        # Проверка необходимости пагинации
        show_pagination = len(filtered_data) > self.paginate_by

        # Передача данных в контекст
        context["claims"] = filtered_data
        context["filters"] = {
            "title": title_filter,
            "date_from": date_from,
            "date_to": date_to,
            "prefix": prefix_filter,
            "judge": judge_filter,
            "note": note_filter,
            "urgent": urgent_filter,
        }
        context["judges"] = judges
        context["show_pagination"] = show_pagination
        return context

    def parse_court_time(self, court_time_str):
        """Парсит строку времени судопроизводства в timedelta."""
        if not court_time_str or court_time_str == "—":
            return timedelta(days=0)
        try:
            days = int(court_time_str.split()[0])
            return timedelta(days=days)
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