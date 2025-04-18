from celery import shared_task
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
from statistics import mean, median
from .models import ForumThreadLink1, ForumThreadLink2, ForumThreadLink3, ThreadMessageLink1, ThreadMessageLink2, ThreadMessageLink3, Judge, WorkHistory, StatSummary
from .utils import format_timedelta_to_hours

@shared_task
def update_stats(source="link2"):
    model_map = {
        "link1": (ForumThreadLink1, ThreadMessageLink1),
        "link2": (ForumThreadLink2, ThreadMessageLink2),
        "link3": (ForumThreadLink3, ThreadMessageLink3),
    }
    thread_model, message_model = model_map.get(source, (ForumThreadLink2, ThreadMessageLink2))
    threads = thread_model.objects.using("parser_db").prefetch_related(f"threadmessagelink{source[-1]}_set").order_by("-created_at")

    # Инициализация статистик
    total_threads = 0
    prefix_counts = {"Рассмотрено": 0, "Отказано": 0, "Важно": 0, "На рассмотрении": 0, "Нет": 0}
    first_response_times = []
    court_times = []
    judge_stats = {}
    threads_by_date = {}

    judges = Judge.objects.using("judges_db").prefetch_related("workhistory_set").all()

    for thread in threads:
        if len(thread.title) <= 5:
            continue
        total_threads += 1
        prefix = thread.prefix or "Нет"
        prefix_counts[prefix] = prefix_counts.get(prefix, 0) + 1

        # Время первого ответа
        messages = message_model.objects.using("parser_db").filter(thread=thread).order_by("posted_at")
        first_response_time = None
        for message in messages:
            for judge in judges:
                if (message.author == judge.forum_account and
                    any(history.start_date <= message.posted_at and
                        (history.end_date is None or history.end_date >= message.posted_at)
                        for history in judge.workhistory_set.all())):
                    first_response_time = (message.posted_at - thread.created_at).total_seconds() / 3600
                    if judge.full_name not in judge_stats:
                        judge_stats[judge.full_name] = {
                            "threads": 0,
                            "first_response_times": [],
                            "court_times": [],
                            "prefix_counts": {"Рассмотрено": 0, "Отказано": 0, "Важно": 0, "На рассмотрении": 0, "Нет": 0}
                        }
                    judge_stats[judge.full_name]["threads"] += 1
                    judge_stats[judge.full_name]["first_response_times"].append(first_response_time)
                    judge_stats[judge.full_name]["prefix_counts"][prefix] += 1
                    break
            if first_response_time is not None:
                break
        if first_response_time is not None:
            first_response_times.append(first_response_time)

        # Время судопроизводства
        final_prefixes = ["Рассмотрено", "Отказано", "Важно"]
        last_response_time = None
        if prefix in final_prefixes:
            last_message = messages.order_by("-posted_at").first()
            if last_message:
                for judge in judges:
                    if (last_message.author == judge.forum_account and
                        any(history.start_date <= last_message.posted_at and
                            (history.end_date is None or history.end_date >= last_message.posted_at)
                            for history in judge.workhistory_set.all())):
                        last_response_time = (last_message.posted_at - thread.created_at).total_seconds() / 3600
                        if judge.full_name in judge_stats:
                            judge_stats[judge.full_name]["court_times"].append(last_response_time)
                        break
        if last_response_time is not None:
            court_times.append(last_response_time)

        # Треды по дате
        date_key = thread.created_at.strftime("%Y-%m-%d")
        threads_by_date[date_key] = threads_by_date.get(date_key, 0) + 1

    # Сохранение статистик
    stats_data = {
        "total_threads": total_threads,
        "prefix_counts": prefix_counts,
        "avg_first_response": mean(first_response_times) if first_response_times else None,
        "median_first_response": median(first_response_times) if first_response_times else None,
        "avg_court_time": mean(court_times) if court_times else None,
        "median_court_time": median(court_times) if court_times else None,
        "judge_stats": {
            name: {
                "threads": data["threads"],
                "avg_first_response": mean(data["first_response_times"]) if data["first_response_times"] else None,
                "avg_court_time": mean(data["court_times"]) if data["court_times"] else None,
                "prefix_counts": data["prefix_counts"]
            } for name, data in judge_stats.items()
        },
        "threads_by_date": threads_by_date
    }

    # Кэширование
    cache.set(f"stats_{source}", stats_data, timeout=300)

    # Сохранение в БД
    StatSummary.objects.update_or_create(
        source=source,
        defaults={
            "total_threads": total_threads,
            "prefix_counts": prefix_counts,
            "avg_first_response": stats_data["avg_first_response"],
            "median_first_response": stats_data["median_first_response"],
            "avg_court_time": stats_data["avg_court_time"],
            "median_court_time": stats_data["median_court_time"],
            "judge_stats": stats_data["judge_stats"],
            "threads_by_date": threads_by_date,
            "updated_at": timezone.now()
        }
    )

    return stats_data