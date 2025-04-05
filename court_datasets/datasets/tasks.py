from celery import shared_task
from .models import ForumThread, ClaimNote
from .utils import get_claim_data
from django.core.cache import cache

@shared_task
def update_claims_data():
    threads = ForumThread.objects.using("parser_db").prefetch_related("threadmessage_set").order_by("-created_at")
    claims_data = []
    for thread in threads:
        claim_data = get_claim_data(thread)
        note = ClaimNote.objects.filter(thread_id=thread.id).first()
        claim_data["note"] = note.note if note else ""
        claim_data["thread_id"] = thread.id
        claims_data.append(claim_data)
    cache.set("claims_data", claims_data, timeout=2)
    return claims_data