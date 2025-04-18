from django.utils import timezone
from datetime import timedelta
from .models import ForumThreadLink1, ForumThreadLink2, ForumThreadLink3, ThreadMessageLink1, ThreadMessageLink2, ThreadMessageLink3, Judge, WorkHistory

def format_timedelta(delta):
    if not delta:
        return "0 д. 0 ч. 0 м."
    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes = remainder // 60
    return f"{days} д. {hours} ч. {minutes} м."

def get_first_court_response(thread, source):
    message_model = {"link1": ThreadMessageLink1, "link2": ThreadMessageLink2, "link3": ThreadMessageLink3}[source]
    messages = message_model.objects.filter(thread=thread).order_by("posted_at")
    judges = Judge.objects.all()
    for message in messages:
        for judge in judges:
            if (message.author == judge.forum_account and
                any(history.start_date <= message.posted_at and
                    (history.end_date is None or history.end_date >= message.posted_at)
                    for history in judge.workhistory_set.all())):
                return message.posted_at
    return timezone.now()

def get_last_court_response(thread, source):
    message_model = {"link1": ThreadMessageLink1, "link2": ThreadMessageLink2, "link3": ThreadMessageLink3}[source]
    messages = message_model.objects.filter(thread=thread).order_by("-posted_at")
    judges = Judge.objects.all()
    for message in messages:
        for judge in judges:
            if (message.author == judge.forum_account and
                any(history.start_date <= message.posted_at and
                    (history.end_date is None or history.end_date >= message.posted_at)
                    for history in judge.workhistory_set.all())):
                return message.posted_at
    return None

def get_leading_judges(thread, source):
    message_model = {"link1": ThreadMessageLink1, "link2": ThreadMessageLink2, "link3": ThreadMessageLink3}[source]
    messages = message_model.objects.filter(thread=thread).select_related("thread")
    judges = Judge.objects.prefetch_related("workhistory_set")
    leading_judges = set()
    for message in messages:
        for judge in judges:
            if (message.author == judge.forum_account and
                any(history.start_date <= message.posted_at and
                    (history.end_date is None or history.end_date >= message.posted_at)
                    for history in judge.workhistory_set.all())):
                leading_judges.add(judge.full_name)
    return ", ".join(leading_judges) if leading_judges else "Не определён"

def is_data_outdated(thread):
    return (timezone.now() - thread.created_at) > timedelta(hours=24)

def get_claim_data(thread, source):
    first_response = get_first_court_response(thread, source)
    last_response = get_last_court_response(thread, source)
    final_prefixes = ["Рассмотрено", "Отказано", "Важно"]

    first_response_time = first_response - thread.created_at if first_response else None
    if thread.prefix in final_prefixes and last_response:
        court_time = last_response - first_response
    else:
        court_time = None if not first_response else (timezone.now() - first_response)

    return {
        "title": thread.title,
        "url": thread.url,
        "created_at": thread.created_at,
        "first_response_time": format_timedelta(first_response_time) if first_response_time else "Нет данных",
        "court_time": format_timedelta(court_time) if court_time else "Нет данных",
        "prefix": thread.prefix or "Нет",
        "status": "В разработке",
        "leading_judges": get_leading_judges(thread, source),
    }