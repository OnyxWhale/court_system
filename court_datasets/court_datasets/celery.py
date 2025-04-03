import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "court_datasets.settings")
app = Celery("court_datasets")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()