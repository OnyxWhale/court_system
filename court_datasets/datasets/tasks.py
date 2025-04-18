from celery import shared_task
from .models import ForumThreadLink1, ForumThreadLink2, ForumThreadLink3, ClaimNote
from .utils import get_claim_data
from django.core.cache import cache

@shared_task
def update_claims_data(source="link2"):
    model_map = {
        "link1": ForumThreadLink1,
        "link2": ForumThreadLink2,
        "link3": ForumThreadLink3,
    }
    model = model_map.get(source, ForumThreadLink2)
    related_name = f"threadmessagelink{source[-1]}_set"
    threads = model.objects.using("parser_db").prefetch_related(related_name).order_by("-created_at")
    claims_data = []
    for thread in threads:
        if len(thread.title) <= 5:
            continue
        claim_data = get_claim_data(thread, source)
        note = ClaimNote.objects.filter(thread_id=thread.id, source=source).first()
        claim_data["note"] = note.note if note else ""
        claim_data["thread_id"] = thread.id
        claim_data["source"] = source
        claims_data.append(claim_data)
    cache.set(f"claims_data_{source}", claims_data, timeout=2)
    return claims_data