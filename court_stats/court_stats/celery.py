import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "court_stats.settings")
app = Celery("court_stats")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()