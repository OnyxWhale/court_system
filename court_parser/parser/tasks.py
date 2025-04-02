import logging
from typing import Optional
from celery import shared_task
from django.utils import timezone
from .parser import ForumParser
from .models import ForumThread, ThreadMessage, ParseProgress

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def parse_forum(self, pages: int) -> None:
    """
    Асинхронная задача для парсинга форума.

    Args:
        self: Экземпляр задачи Celery (для bind=True).
        pages (int): Количество страниц для парсинга, заданное пользователем.

    Raises:
        Exception: При ошибке парсинга с повторной попыткой через 60 секунд.
    """
    try:
        parser = ForumParser()
        progress, _ = ParseProgress.objects.get_or_create(
            id=1, defaults={"status": "running"}
        )
        progress.task_id = self.request.id
        progress.status = "running"
        progress.total_threads = 0  # Инициализация общего количества тредов
        progress.processed_threads = 0
        progress.progress = 0.0
        progress.save()

        # Парсинг всех тредов
        all_threads = parser.parse_all_threads(pages)
        progress.total_threads = len(all_threads)

        for thread_data in all_threads:
            thread, _ = ForumThread.objects.update_or_create(
                url=thread_data["url"],
                defaults={
                    "title": thread_data["title"],
                    "prefix": thread_data.get("prefix", ""),
                    "created_at": thread_data["created_at"],
                    "updated_at": timezone.now(),
                }
            )
            messages = parser.parse_messages(thread_data["url"])
            for message_data in messages:
                ThreadMessage.objects.update_or_create(
                    url=message_data["url"],
                    defaults={
                        "thread": thread,
                        "author": message_data["author"],
                        "content": message_data["content"],
                        "posted_at": message_data["posted_at"],
                    }
                )
            progress.processed_threads += 1
            progress.progress = (
                progress.processed_threads / progress.total_threads * 100
                if progress.total_threads > 0
                else 100.0
            )
            progress.save()

        progress.status = "completed"
        progress.progress = 100.0
        progress.task_id = None
        progress.save()
        logger.info(f"Парсинг {pages} страниц успешно завершён")
    except Exception as e:
        logger.error(f"Ошибка парсинга: {e}")
        self.retry(countdown=60)  # Повтор через 60 секунд