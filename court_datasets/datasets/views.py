from django.views.generic import ListView
from django.http import JsonResponse, HttpResponseServerError
from .models import ForumThread, ClaimNote
from .utils import get_claim_data
from django.db import connections
from django.db.utils import OperationalError
from .tasks import update_claims_data
from django.core.cache import cache
from celery.exceptions import OperationalError as CeleryOperationalError

class DatasetsListView(ListView):
    model = ForumThread
    template_name = "datasets/datasets_list.html"
    context_object_name = "claims"
    paginate_by = 100

    def get_queryset(self):
        try:
            connections["parser_db"].ensure_connection()
            return ForumThread.objects.using("parser_db").prefetch_related("threadmessage_set").order_by("-created_at")
        except OperationalError as e:
            print(f"Ошибка подключения к parser_db: {e}")
            return ForumThread.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        claims_data = cache.get("claims_data")
        if not claims_data:
            try:
                update_claims_data.delay()
                print("Задача отправлена в Celery, данные пока недоступны.")
            except CeleryOperationalError as e:
                print(f"Ошибка Celery: {e}. Используем прямую обработку данных.")
                claims_data = []
                for thread in self.get_queryset():  # Порядок из get_queryset сохраняется
                    claim_data = get_claim_data(thread)
                    note = ClaimNote.objects.filter(thread_id=thread.id).first()
                    claim_data["note"] = note.note if note else ""
                    claim_data["thread_id"] = thread.id
                    claims_data.append(claim_data)
                cache.set("claims_data", claims_data, timeout=3600)
        context["claims"] = claims_data
        return context

def update_note(request):
    if request.method == "POST":
        thread_id = request.POST.get("thread_id")
        note_text = request.POST.get("note").strip()
        try:
            if note_text:
                note, _ = ClaimNote.objects.update_or_create(thread_id=thread_id, defaults={"note": note_text})
            else:
                ClaimNote.objects.filter(thread_id=thread_id).delete()
            return JsonResponse({"success": True})
        except Exception as e:
            print(f"Error in update_note: {e}")
            return JsonResponse({"success": False, "error": str(e)})
    return JsonResponse({"success": False, "error": "Invalid request"})