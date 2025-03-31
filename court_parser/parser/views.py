from django.views.generic import TemplateView, ListView, DetailView
from django.urls import reverse_lazy
from django.http import JsonResponse
from .models import ForumThread, ThreadMessage, ParseProgress
from .tasks import parse_forum
from django_celery_beat.models import PeriodicTask, IntervalSchedule

class ParserHomeView(TemplateView):
    template_name = "parser/home.html"

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        if action == "manual_parse":
            pages = int(request.POST.get("pages", 1))
            parse_forum.delay(pages)
            return JsonResponse({"message": "Ручной парсинг запущен."})
        elif action == "auto_parse":
            pages = int(request.POST.get("pages", 1))
            interval = int(request.POST.get("interval", 60))  # Интервал в минутах
            schedule, _ = IntervalSchedule.objects.get_or_create(
                every=interval,
                period=IntervalSchedule.MINUTES
            )
            PeriodicTask.objects.update_or_create(
                name="Auto Parse Forum",
                defaults={
                    "interval": schedule,
                    "task": "parser.tasks.parse_forum",
                    "args": [pages],  # Список напрямую
                }
            )
            return JsonResponse({"message": f"Автоматический парсинг запущен: {pages} страниц каждые {interval} минут."})
        return JsonResponse({"error": "Неверное действие."}, status=400)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        progress = ParseProgress.objects.first()
        context["progress"] = progress
        # Проверяем настройки автоматического парсинга с защитой от None
        auto_task = PeriodicTask.objects.filter(name="Auto Parse Forum").first()
        if auto_task and auto_task.args:
            context["auto_parse"] = {
                "pages": auto_task.args[0],
                "interval": auto_task.interval.every
            }
        else:
            context["auto_parse"] = None
        return context

class ThreadListView(ListView):
    model = ForumThread
    template_name = "parser/threads.html"
    context_object_name = "threads"
    paginate_by = 84

    def get_queryset(self):
        return ForumThread.objects.prefetch_related("threadmessage_set").order_by("-created_at")

class ThreadDetailView(DetailView):
    model = ForumThread
    template_name = "parser/thread_detail.html"
    context_object_name = "thread"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["messages"] = ThreadMessage.objects.filter(thread=self.object)
        return context