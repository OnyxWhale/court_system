import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "court_parser.settings")
app = Celery("court_parser")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()