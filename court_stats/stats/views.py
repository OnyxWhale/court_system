from django.views.generic import TemplateView
from django.core.cache import cache
from django.db.models.functions import Length
from .models import ForumThreadLink1, ForumThreadLink2, ForumThreadLink3, Judge, StatSummary
from .tasks import update_stats
from .utils import format_timedelta_to_hours
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class StatsListView(TemplateView):
    template_name = "stats/stats_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        source = self.request.GET.get("source", "link2")
        date_from = self.request.GET.get("date_from")
        date_to = self.request.GET.get("date_to")
        judge_filter = self.request.GET.get("judge")
        prefix_filter = self.request.GET.get("prefix")

        # Получение данных из кэша или БД
        stats_data = cache.get(f"stats_{source}")
        if not stats_data:
            stats_summary = StatSummary.objects.filter(source=source).first()
            if stats_summary:
                stats_data = {
                    "total_threads": stats_summary.total_threads,
                    "prefix_counts": stats_summary.prefix_counts,
                    "avg_first_response": stats_summary.avg_first_response,
                    "median_first_response": stats_summary.median_first_response,
                    "avg_court_time": stats_summary.avg_court_time,
                    "median_court_time": stats_summary.median_court_time,
                    "judge_stats": stats_summary.judge_stats,
                    "threads_by_date": stats_summary.threads_by_date
                }
                cache.set(f"stats_{source}", stats_data, timeout=300)
            else:
                stats_data = {
                    "total_threads": 0,
                    "prefix_counts": {"Рассмотрено": 0, "Отказано": 0, "Важно": 0, "На рассмотрении": 0, "Нет": 0},
                    "avg_first_response": None,
                    "median_first_response": None,
                    "avg_court_time": None,
                    "median_court_time": None,
                    "judge_stats": {},
                    "threads_by_date": {}
                }

        # Фильтрация
        model_map = {
            "link1": ForumThreadLink1,
            "link2": ForumThreadLink2,
            "link3": ForumThreadLink3
        }
        model = model_map.get(source, ForumThreadLink2)
        threads = model.objects.using("parser_db").annotate(title_length=Length("title")).filter(title_length__gt=5)
        if date_from:
            threads = threads.filter(created_at__gte=date_from)
        if date_to:
            threads = threads.filter(created_at__lte=date_to)
        if prefix_filter:
            threads = threads.filter(prefix=prefix_filter)

        # Фильтрация по судье
        filtered_judge_stats = stats_data["judge_stats"]
        if judge_filter:
            filtered_judge_stats = {name: data for name, data in stats_data["judge_stats"].items() if name.lower() == judge_filter.lower()}

        # Подготовка данных для графиков
        chart_data = {
            "prefix_labels": list(stats_data["prefix_counts"].keys()),
            "prefix_values": list(stats_data["prefix_counts"].values()),
            "date_labels": sorted(stats_data["threads_by_date"].keys()),
            "date_values": [stats_data["threads_by_date"][k] for k in sorted(stats_data["threads_by_date"].keys())]
        }

        # Список судей
        judges = Judge.objects.using("judges_db").values_list("full_name", flat=True).distinct()

        context.update({
            "stats": stats_data,
            "source": source,
            "court_name": {"link1": "Верховный суд", "link2": "Федеральный суд", "link3": "Реабилитации"}[source],
            "filters": {
                "source": source,
                "date_from": date_from or "",
                "date_to": date_to or "",
                "judge": judge_filter or "",
                "prefix": prefix_filter or ""
            },
            "judges": judges,
            "chart_data": chart_data,
            "format_timedelta": format_timedelta_to_hours
        })

        # Запуск обновления статистики
        update_stats.delay(source)
        return context