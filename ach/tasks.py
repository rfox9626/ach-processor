from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings

from ach.scanner import claim_ready_files

from .models import Entry
from .services import chunked, evaluate_entries, ingest_file

logger = get_task_logger(__name__)


@shared_task
def process_file(path):
    ach_file = ingest_file(path)

    ids = list(
        Entry.objects
        .filter(ach_file=ach_file, status=Entry.Status.PENDING)
        .order_by("id")
        .values_list("id", flat=True)
    )

    valid_cnt = 0
    invalid_cnt = 0

    for chunk in chunked(ids, settings.ACH_CHUNK_SIZE):
        summary = evaluate_entries(chunk)
        valid_cnt += summary["valid"]
        invalid_cnt += summary["invalid"]

    logger.info("Loaded %s as file %s, valid=%d, invalid=%d", path, 
                ach_file.id, valid_cnt, invalid_cnt)

    return ach_file.id


# ach/tasks.py: the Celery wrapper
@shared_task
def scan_incoming():
    claimed = claim_ready_files(settings.ACH_INCOMING_DIR, settings.ACH_PROCESSING_DIR)
    for path in claimed:
        process_file.delay(str(path))
    return len(claimed)
