from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings

from ach.scanner import claim_ready_files
from ach.services import ingest_file

logger = get_task_logger(__name__)


@shared_task
def process_file(path):
    ach_file = ingest_file(path)
    logger.info("Loaded %s as file %s", path, ach_file.id)
    return ach_file.id


# ach/tasks.py: the Celery wrapper
@shared_task
def scan_incoming():
    claimed = claim_ready_files(settings.ACH_INCOMING_DIR, settings.ACH_PROCESSING_DIR)
    for path in claimed:
        process_file.delay(str(path))
    return len(claimed)
