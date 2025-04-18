import logging
from typing import Optional
from celery import shared_task, group
from django.utils import timezone
from .parser import ForumParser
from .models import (
    ForumThreadLink1, ThreadMessageLink1, ForumThreadLink2, ThreadMessageLink2,
    ForumThreadLink3, ThreadMessageLink3, ParseProgress
)
from django_celery_beat.models import PeriodicTask

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def parse_forum_link(self, pages: int, link_type: str) -> None:
    """
    Асинхронная задача для парсинга форума по одной ссылке.

    Args:
        self: Экземпляр задачи Celery (для bind=True).
        pages (int): Количество страниц для парсинга.
        link_type (str): Тип ссылки ('link1', 'link2', 'link3').

    Raises:
        Exception: При ошибке парсинга с повторной попыткой через 60 секунд.
    """
    logger.info(f"Starting parse_forum_link with pages={pages}, link_type={link_type}")
    try:
        parser = ForumParser(link_type)
        progress, _ = ParseProgress.objects.get_or_create(
            link_type=link_type, defaults={"status": "running"}
        )
        progress.task_id = self.request.id
        progress.status = "running"
        progress.total_threads = 0
        progress.processed_threads = 0
        progress.progress = 0.0
        progress.save()

        # Определяем модели в зависимости от link_type
        thread_model = {
            'link1': ForumThreadLink1,
            'link2': ForumThreadLink2,
            'link3': ForumThreadLink3
        }[link_type]
        message_model = {
            'link1': ThreadMessageLink1,
            'link2': ThreadMessageLink2,
            'link3': ThreadMessageLink3
        }[link_type]

        # Парсинг всех тредов
        all_threads = parser.parse_all_threads(pages)
        progress.total_threads = len(all_threads)

        for thread_data in all_threads:
            thread, _ = thread_model.objects.update_or_create(
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
                message_model.objects.update_or_create(
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

        # Обновляем статус и время последнего запуска
        progress.status = "completed"
        progress.progress = 100.0
        progress.task_id = None
        progress.save()

        # Обновляем время последнего запуска для PeriodicTask
        auto_task = PeriodicTask.objects.filter(name=f"Auto Parse Forum {link_type}").first()
        if auto_task:
            auto_task.last_run_at = timezone.now()
            auto_task.save()

        logger.info(f"Парсинг {pages} страниц для {link_type} успешно завершён")
    except Exception as e:
        logger.error(f"Ошибка парсинга {link_type}: {e}")
        progress.status = "failed"
        progress.save()
        self.retry(countdown=60)

@shared_task
def parse_forum(pages: int) -> None:
    """
    Запускает параллельный парсинг для всех трёх ссылок.

    Args:
        pages (int): Количество страниц для парсинга.
    """
    tasks = [
        parse_forum_link.s(pages, link_type)
        for link_type in ['link1', 'link2', 'link3']
    ]
    group(tasks).apply_async()