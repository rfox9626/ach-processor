import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ach_processor.settings")

app = Celery("ach_processor")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@app.task
def ping():
    return "pong"
