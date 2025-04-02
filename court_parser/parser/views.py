import json
import logging
from typing import Dict, Optional, Tuple
from django.views.generic import TemplateView, ListView, DetailView
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from .models import ForumThread, ThreadMessage, ParseProgress
from .tasks import parse_forum
from django_celery_beat.models import PeriodicTask, IntervalSchedule

logger = logging.getLogger(__name__)

def get_auto_parse_info(auto_task: Optional[PeriodicTask]) -> Tuple[Optional[Dict], Optional[timezone.datetime]]:
    """
    Получает информацию об автоматическом парсинге.

    Args:
        auto_task (Optional[PeriodicTask]): Задача автоматического парсинга.

    Returns:
        Tuple[Optional[Dict], Optional[datetime]]: Информация о парсинге и время следующего запуска.
    """
    if not auto_task or not auto_task.args:
        return None, None
    try:
        args = json.loads(auto_task.args)
        last_run = auto_task.last_run_at or timezone.now()
        next_run = last_run + timedelta(minutes=auto_task.interval.every)
        return {"pages": args[0], "interval": auto_task.interval.every}, next_run
    except (json.JSONDecodeError, IndexError) as e:
        logger.error(f"Ошибка при парсинге args: {e}")
        return None, None

class ParserHomeView(TemplateView):
    template_name = "parser/home.html"

    def post(self, request, *args, **kwargs) -> JsonResponse:
        """
        Обрабатывает POST-запросы для управления парсингом.

        Args:
            request: HTTP-запрос.
            *args: Дополнительные аргументы.
            **kwargs: Дополнительные именованные аргументы.

        Returns:
            JsonResponse: Ответ с результатом действия.
        """
        action = request.POST.get("action")
        if action == "auto_parse":
            try:
                pages = int(request.POST.get("pages", "1"))
                interval = int(request.POST.get("interval", "60"))
                if pages < 1 or interval < 1:
                    raise ValueError("Количество страниц и интервал должны быть положительными")
            except ValueError as e:
                return JsonResponse({"error": str(e)}, status=400)

            schedule, _ = IntervalSchedule.objects.get_or_create(
                every=interval, period=IntervalSchedule.MINUTES
            )
            PeriodicTask.objects.update_or_create(
                name="Auto Parse Forum",
                defaults={
                    "interval": schedule,
                    "task": "parser.tasks.parse_forum",
                    "args": json.dumps([pages]),
                }
            )
            progress, _ = ParseProgress.objects.get_or_create(
                id=1, defaults={"status": "running"}
            )
            progress.status = "running"
            progress.save()
            logger.info(f"Автоматический парсинг запущен: {pages} страниц каждые {interval} минут")
            return JsonResponse({"message": "Статус: Работает"})
        elif action == "stop_auto_parse":
            PeriodicTask.objects.filter(name="Auto Parse Forum").delete()
            progress = ParseProgress.objects.first()
            if progress and progress.task_id:
                try:
                    from celery import current_app
                    control = current_app.control
                    control.revoke(progress.task_id, terminate=True)
                    logger.info(f"Задача с task_id {progress.task_id} завершена")
                except Exception as e:
                    logger.error(f"Ошибка при завершении задачи: {e}")
            if progress:
                progress.status = "stopped"
                progress.task_id = None
                progress.save()
            logger.info("Автоматический парсинг остановлен")
            return JsonResponse({"message": "Статус: Не активен"})
        return JsonResponse({"error": "Неверное действие"}, status=400)

    def get_context_data(self, **kwargs) -> Dict:
        """
        Возвращает контекст для шаблона.

        Args:
            **kwargs: Дополнительные именованные аргументы.

        Returns:
            Dict: Контекст для рендеринга шаблона.
        """
        context = super().get_context_data(**kwargs)
        progress = ParseProgress.objects.first()
        auto_task = PeriodicTask.objects.filter(name="Auto Parse Forum").first()
        context["progress"] = progress
        context["auto_parse"], context["next_run"] = get_auto_parse_info(auto_task)
        return context

class ThreadListView(ListView):
    model = ForumThread
    template_name = "parser/threads.html"
    context_object_name = "threads"
    paginate_by = 84

    def get_queryset(self):
        """
        Возвращает набор данных для списка тредов.

        Returns:
            QuerySet: Отсортированный набор тредов.
        """
        return ForumThread.objects.prefetch_related("threadmessage_set").order_by("-created_at")

class ThreadDetailView(DetailView):
    model = ForumThread
    template_name = "parser/thread_detail.html"
    context_object_name = "thread"

    def get_context_data(self, **kwargs) -> Dict:
        """
        Возвращает контекст для детального просмотра треда.

        Args:
            **kwargs: Дополнительные именованные аргументы.

        Returns:
            Dict: Контекст для рендеринга шаблона.
        """
        context = super().get_context_data(**kwargs)
        context["messages"] = ThreadMessage.objects.filter(thread=self.object)
        return context

def parser_status(request) -> JsonResponse:
    """
    Возвращает статус парсинга в формате JSON.

    Args:
        request: HTTP-запрос.

    Returns:
        JsonResponse: Статус парсинга и автоматического парсинга.
    """
    progress = ParseProgress.objects.first()
    auto_task = PeriodicTask.objects.filter(name="Auto Parse Forum").first()
    auto_parse, next_run = get_auto_parse_info(auto_task)
    data = {
        "progress": {
            "status": progress.status if progress else "Не активен",
            "progress": progress.progress if progress else 0
        },
        "auto_parse": auto_parse,
        "next_run": next_run.strftime("%Y-%m-%d %H:%M:%S") if next_run else "Автоматический парсинг не активен"
    }
    return JsonResponse(data)