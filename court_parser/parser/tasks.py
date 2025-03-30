from celery import shared_task
from .parser import ForumParser
from .models import ForumThread, ThreadMessage, ParseProgress

@shared_task
def parse_forum(pages):
    parser = ForumParser()
    progress, _ = ParseProgress.objects.get_or_create(id=1, defaults={"status": "running"})

    # Парсинг тредов со всех страниц
    threads = parser.parse_all_threads(pages)
    if not threads:
        progress.status = "failed"
        progress.save()
        return

    progress.total_threads = len(threads)
    progress.save()

    # Сохранение тредов и сообщений
    for i, thread_data in enumerate(threads):
        thread, _ = ForumThread.objects.update_or_create(
            url=thread_data["url"],
            defaults={
                "title": thread_data["title"],
                "prefix": thread_data["prefix"],
                "created_at": thread_data["created_at"],
                "updated_at": thread_data["updated_at"],
            }
        )
        messages = parser.parse_messages(thread.url)
        for msg_data in messages:
            ThreadMessage.objects.update_or_create(
                thread=thread, url=msg_data["url"], author=msg_data["author"],
                defaults={"content": msg_data["content"], "posted_at": msg_data["posted_at"]}
            )
        progress.processed_threads = i + 1
        progress.progress = (progress.processed_threads / progress.total_threads) * 100
        progress.status = "running"
        progress.save()

    progress.status = "completed"
    progress.save()