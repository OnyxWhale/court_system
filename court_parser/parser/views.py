import json
import logging
from typing import Dict, Optional, Tuple
from django.views.generic import TemplateView, ListView, DetailView
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from .models import (
    ParseProgress,
    ForumThreadLink1, ThreadMessageLink1,
    ForumThreadLink2, ThreadMessageLink2,
    ForumThreadLink3, ThreadMessageLink3
)
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
        logger.debug(f"No auto_task or empty args: {auto_task}")
        return None, None
    try:
        args = json.loads(auto_task.args)
        logger.debug(f"Parsed args: {args}")
        if not isinstance(args, list) or len(args) < 2:
            logger.error(f"Invalid args format, expected [pages, link_type]: {args}")
            return None, None
        pages, link_type = args[0], args[1]
        if not isinstance(pages, int) or not isinstance(link_type, str):
            logger.error(f"Invalid args types, expected [int, str]: {args}")
            return None, None
        last_run = auto_task.last_run_at or timezone.now()
        next_run = last_run + timedelta(minutes=auto_task.interval.every)
        return {"pages": pages, "interval": auto_task.interval.every}, next_run
    except (json.JSONDecodeError, IndexError, TypeError) as e:
        logger.error(f"Error parsing args: {e}, args: {auto_task.args}")
        return None, None

class ParserHomeView(TemplateView):
    template_name = "parser/home.html"

    def post(self, request, *args, **kwargs) -> JsonResponse:
        action = request.POST.get("action")
        if action == "auto_parse":
            try:
                pages = int(request.POST.get("pages", "1"))
                interval = int(request.POST.get("interval", "60"))
                if pages < 1 or interval < 1:
                    raise ValueError("Количество страниц и интервал должны быть положительными")
            except ValueError as e:
                logger.error(f"Invalid input: {e}")
                return JsonResponse({"error": str(e)}, status=400)

            schedule, _ = IntervalSchedule.objects.get_or_create(
                every=interval, period=IntervalSchedule.MINUTES
            )
            for link_type in ['link1', 'link2', 'link3']:
                PeriodicTask.objects.update_or_create(
                    name=f"Auto Parse Forum {link_type}",
                    defaults={
                        "interval": schedule,
                        "task": "parser.tasks.parse_forum_link",
                        "args": json.dumps([pages, link_type]),
                    }
                )
                progress, _ = ParseProgress.objects.get_or_create(
                    link_type=link_type, defaults={"status": "running"}
                )
                progress.status = "running"
                progress.save()
            logger.info(f"Автоматический парсинг запущен: {pages} страниц каждые {interval} минут")
            return JsonResponse({"message": "Статус: Работает"})
        elif action == "stop_auto_parse":
            for link_type in ['link1', 'link2', 'link3']:
                PeriodicTask.objects.filter(name=f"Auto Parse Forum {link_type}").delete()
                progress = ParseProgress.objects.filter(link_type=link_type).first()
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
        context = super().get_context_data(**kwargs)
        progresses = ParseProgress.objects.all()
        auto_tasks = {task.name: task for task in PeriodicTask.objects.filter(name__startswith="Auto Parse Forum")}
        context["progresses"] = progresses
        context["auto_parse"] = None
        context["next_run"] = None
        if auto_tasks:
            auto_task = list(auto_tasks.values())[0]
            context["auto_parse"], context["next_run"] = get_auto_parse_info(auto_task)
        return context

class ThreadListLink1View(ListView):
    model = ForumThreadLink1
    template_name = "parser/link1_threads.html"
    context_object_name = "threads"
    paginate_by = 84

    def get_queryset(self):
        return ForumThreadLink1.objects.prefetch_related("threadmessagelink1_set").order_by("-created_at")

class ThreadDetailLink1View(DetailView):
    model = ForumThreadLink1
    template_name = "parser/link1_thread_detail.html"
    context_object_name = "thread"

    def get_context_data(self, **kwargs) -> Dict:
        context = super().get_context_data(**kwargs)
        context["messages"] = ThreadMessageLink1.objects.filter(thread=self.object)
        return context

class ThreadListLink2View(ListView):
    model = ForumThreadLink2
    template_name = "parser/link2_threads.html"
    context_object_name = "threads"
    paginate_by = 84

    def get_queryset(self):
        return ForumThreadLink2.objects.prefetch_related("threadmessagelink2_set").order_by("-created_at")

class ThreadDetailLink2View(DetailView):
    model = ForumThreadLink2
    template_name = "parser/link2_thread_detail.html"
    context_object_name = "thread"

    def get_context_data(self, **kwargs) -> Dict:
        context = super().get_context_data(**kwargs)
        context["messages"] = ThreadMessageLink2.objects.filter(thread=self.object)
        return context

class ThreadListLink3View(ListView):
    model = ForumThreadLink3
    template_name = "parser/link3_threads.html"
    context_object_name = "threads"
    paginate_by = 84

    def get_queryset(self):
        return ForumThreadLink3.objects.prefetch_related("threadmessagelink3_set").order_by("-created_at")

class ThreadDetailLink3View(DetailView):
    model = ForumThreadLink3
    template_name = "parser/link3_thread_detail.html"
    context_object_name = "thread"

    def get_context_data(self, **kwargs) -> Dict:
        context = super().get_context_data(**kwargs)
        context["messages"] = ThreadMessageLink3.objects.filter(thread=self.object)
        return context

def parser_status(request) -> JsonResponse:
    """
    Возвращает статус парсинга для всех типов ссылок и информацию об автоматическом парсинге.

    Args:
        request: HTTP-запрос.

    Returns:
        JsonResponse: JSON с данными о прогрессе, настройках и времени до следующего парсинга.
    """
    progresses = ParseProgress.objects.all()
    auto_tasks = PeriodicTask.objects.filter(name__startswith="Auto Parse Forum")
    auto_parse_info = None
    auto_parse_settings = None
    remaining_time = 0

    if auto_tasks:
        auto_task = auto_tasks.first()
        auto_parse_info, next_run = get_auto_parse_info(auto_task)
        if auto_parse_info:
            auto_parse_settings = {
                "pages": auto_parse_info["pages"],
                "interval": auto_parse_info["interval"]
            }
        if next_run:
            remaining_time = int((next_run - timezone.now()).total_seconds())

    progress_data = [
        {
            "link_type": progress.get_link_type_display(),
            "status": progress.status,
            "progress": progress.progress,
        }
        for progress in progresses
    ]

    return JsonResponse({
        "progresses": progress_data,
        "auto_parse": bool(auto_parse_info),
        "auto_parse_settings": auto_parse_settings,
        "remaining_time": remaining_time,
    })