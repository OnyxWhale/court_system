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
import logging

# Настройка логирования
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
        claims_data = []

        logger.debug(f"Processing threads for source={self.source}, thread count: {all_threads.count()}")
        for thread in all_threads:
            try:
                claim_data = get_claim_data(thread, self.source)
                note = ClaimNote.objects.filter(thread_id=thread.id, source=self.source).first()
                claim_data["note"] = note.note if note else ""
                claim_data["thread_id"] = thread.id
                claim_data["source"] = self.source
                claims_data.append(claim_data)
            except (OperationalError, ProgrammingError) as e:
                logger.error(f"Ошибка обработки треда {thread.id} для source={self.source}: {e}")
                continue

        judge_filter = self.request.GET.get("judge", "").strip()
        urgent_filter = self.request.GET.get("urgent")
        filtered_claims = claims_data

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

        paginator = Paginator(filtered_claims, self.paginate_by)
        page_number = self.request.GET.get("page")
        try:
            page_obj = paginator.page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        judges = sorted(set(claim["leading_judges"] for claim in claims_data if claim["leading_judges"]))

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

        update_claims_data.delay(self.source)

        logger.debug(f"Context prepared for source={self.source}, claims count: {len(claims_data)}")
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

def update_note(request):
    if request.method == "POST":
        thread_id = request.POST.get("thread_id")
        note_text = request.POST.get("note").strip()
        source = request.POST.get("source", "link2")
        try:
            if note_text:
                note, _ = ClaimNote.objects.update_or_create(
                    thread_id=thread_id, source=source, defaults={"note": note_text}
                )
            else:
                ClaimNote.objects.filter(thread_id=thread_id, source=source).delete()
            return JsonResponse({"success": True})
        except Exception as e:
            logger.error(f"Ошибка в update_note для thread_id={thread_id}, source={source}: {e}")
            return JsonResponse({"success": False, "error": str(e)})
    return JsonResponse({"success": False, "error": "Invalid request"})