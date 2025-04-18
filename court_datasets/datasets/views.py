from django.views.generic import ListView
from django.http import JsonResponse
from django.db.models.functions import Length
from .models import ForumThreadLink1, ForumThreadLink2, ForumThreadLink3, ClaimNote
from .utils import get_claim_data
from django.db import connections
from django.db.utils import OperationalError, ProgrammingError
from .tasks import update_claims_data
from datetime import datetime, timedelta
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.cache import cache
import logging
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import ClaimNote
from django.db import transaction

logger = logging.getLogger(__name__)

class BaseDatasetsListView(ListView):
    template_name = "datasets/datasets_list.html"
    context_object_name = "claims"
    paginate_by = 100
    allow_empty = True
    model = None
    source = None
    court_name = None

    def get_queryset(self):
        try:
            connections["parser_db"].ensure_connection()
            related_name = f"threadmessagelink{self.source[-1]}_set"
            logger.debug(f"Querying model {self.model.__name__} with related_name {related_name}")
            queryset = self.model.objects.using("parser_db").prefetch_related(related_name).order_by("-created_at")
            queryset = queryset.annotate(title_length=Length("title")).filter(title_length__gt=5)

            title_filter = self.request.GET.get("title", "").strip()
            date_from = self.request.GET.get("date_from")
            date_to = self.request.GET.get("date_to")
            prefix_filter = self.request.GET.get("prefix")
            note_filter = self.request.GET.get("note")

            if title_filter:
                queryset = queryset.filter(title__icontains=title_filter)
            if date_from:
                queryset = queryset.filter(created_at__gte=date_from)
            if date_to:
                queryset = queryset.filter(created_at__lte=date_to)
            if prefix_filter:
                queryset = queryset.filter(prefix=prefix_filter)
            if note_filter == "with":
                queryset = queryset.filter(claimnote__note__isnull=False, claimnote__source=self.source)
            elif note_filter == "without":
                queryset = queryset.filter(claimnote__note__isnull=True, claimnote__source=self.source)

            logger.debug(f"Queryset count: {queryset.count()}")
            return queryset
        except (OperationalError, ProgrammingError) as e:
            logger.error(f"Ошибка при запросе к parser_db для source={self.source}: {e}")
            return self.model.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_threads = self.get_queryset()
        
        # Проверка кэша
        claims_data = cache.get(f"claims_data_{self.source}")
        if claims_data is None:
            logger.info(f"Cache miss for source={self.source}, running synchronous update")
            claims_data = update_claims_data(self.source)  # Синхронный вызов
        else:
            logger.debug(f"Cache hit for source={self.source}, {len(claims_data)} items retrieved")

        # Фильтрация claims_data в соответствии с queryset
        filtered_claims = []
        thread_ids = {thread.id for thread in all_threads}
        for claim in claims_data:
            if claim["thread_id"] in thread_ids:
                filtered_claims.append(claim)

        judge_filter = self.request.GET.get("judge", "").strip()
        urgent_filter = self.request.GET.get("urgent")
        if judge_filter or urgent_filter == "true":
            temp_claims = []
            for claim in filtered_claims:
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
                temp_claims.append(claim)
            filtered_claims = temp_claims

        paginator = Paginator(filtered_claims, self.paginate_by)
        page_number = self.request.GET.get("page")
        try:
            page_obj = paginator.page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        judges = sorted(set(claim["leading_judges"] for claim in filtered_claims if claim["leading_judges"]))

        context["claims"] = page_obj.object_list
        context["page_obj"] = page_obj
        context["paginator"] = paginator
        context["court_name"] = self.court_name
        context["source"] = self.source
        context["filters"] = {
            "title": self.request.GET.get("title", ""),
            "date_from": self.request.GET.get("date_from"),
            "date_to": self.request.GET.get("date_to"),
            "prefix": self.request.GET.get("prefix"),
            "judge": judge_filter,
            "note": self.request.GET.get("note"),
            "urgent": urgent_filter,
        }
        context["judges"] = judges
        context["is_paginated"] = paginator.num_pages > 1

        # Запуск асинхронного обновления для следующего цикла
        update_claims_data.delay(self.source)

        logger.debug(f"Context prepared for source={self.source}, claims count: {len(filtered_claims)}")
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

class SupremeCourtListView(BaseDatasetsListView):
    model = ForumThreadLink1
    source = "link1"
    court_name = "Верховный суд"

class FederalCourtListView(BaseDatasetsListView):
    model = ForumThreadLink2
    source = "link2"
    court_name = "Федеральный суд"

class RehabilitationListView(BaseDatasetsListView):
    model = ForumThreadLink3
    source = "link3"
    court_name = "Реабилитации"

@csrf_exempt
def update_note(request):
    if request.method != "POST":
        logger.error("Invalid request method for update_note")
        return JsonResponse({"success": False, "error": "Only POST requests are allowed"}, status=405)

    thread_id = request.POST.get("thread_id")
    note_text = request.POST.get("note", "").strip()
    source = request.POST.get("source", "link2")

    # Валидация входных данных
    if not thread_id or not source:
        logger.error(f"Missing required parameters: thread_id={thread_id}, source={source}")
        return JsonResponse({"success": False, "error": "thread_id and source are required"}, status=400)

    try:
        thread_id = int(thread_id)
        if source not in ["link1", "link2", "link3"]:
            raise ValueError(f"Invalid source value: {source}")
    except (ValueError, TypeError) as e:
        logger.error(f"Invalid thread_id={thread_id} or source={source}: {e}")
        return JsonResponse({"success": False, "error": "Invalid thread_id or source"}, status=400)

    try:
        # Проверка существования треда в parser_db
        model_map = {
            "link1": ForumThreadLink1,
            "link2": ForumThreadLink2,
            "link3": ForumThreadLink3,
        }
        model = model_map[source]
        if not model.objects.using("parser_db").filter(id=thread_id).exists():
            logger.error(f"Thread with id={thread_id} not found in source={source}")
            return JsonResponse({"success": False, "error": f"Thread with id={thread_id} not found"}, status=404)

        # Обновление или удаление примечания
        with transaction.atomic():
            if note_text:
                note, created = ClaimNote.objects.using("default").update_or_create(
                    thread_id=thread_id,
                    source=source,
                    defaults={"note": note_text}
                )
                action = "created" if created else "updated"
                logger.info(f"Note {action} for thread_id={thread_id}, source={source}, note={note_text[:50]}")
            else:
                deleted = ClaimNote.objects.using("default").filter(thread_id=thread_id, source=source).delete()[0]
                logger.info(f"Note deleted for thread_id={thread_id}, source={source}, count={deleted}")
        return JsonResponse({"success": True, "message": "Note updated successfully"})
    except Exception as e:
        logger.exception(f"Error updating note for thread_id={thread_id}, source={source}: {str(e)}")
        return JsonResponse({"success": False, "error": f"Database error: {str(e)}"}, status=500)