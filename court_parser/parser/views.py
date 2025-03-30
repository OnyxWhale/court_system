from django.views.generic import TemplateView, ListView, DetailView
from django.urls import reverse_lazy
from .models import ForumThread, ThreadMessage, ParseProgress
from .tasks import parse_forum

class ParserHomeView(TemplateView):
    template_name = "parser/home.html"

    def post(self, request, *args, **kwargs):
        pages = int(request.POST.get("pages", 1))
        parse_forum.delay(pages)
        return self.render_to_response({"message": "Парсинг запущен в фоновом режиме."})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        progress = ParseProgress.objects.first()
        context["progress"] = progress
        return context

class ThreadListView(ListView):
    model = ForumThread
    template_name = "parser/threads.html"
    context_object_name = "threads"
    paginate_by = 84  # 84 треда на страницу

class ThreadDetailView(DetailView):
    model = ForumThread
    template_name = "parser/thread_detail.html"
    context_object_name = "thread"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["messages"] = ThreadMessage.objects.filter(thread=self.object)
        return context