from celery import chain, chord, group, shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.db import transaction

from ach.scanner import claim_ready_files

from .models import AchFile, Entry
from .services import chunked, evaluate_entries, ingest_file

logger = get_task_logger(__name__)


@shared_task(bind=True)
def check_file(self, file_id):
    ids = list(
        Entry.objects
        .filter(ach_file=file_id, status=Entry.Status.PENDING)
        .order_by("id")
        .values_list("id", flat=True)
    )

    if not ids:
        finalize_file([], file_id)
        return None

    chunks = chunked(ids, settings.ACH_CHUNK_SIZE)
    header = group(check_entries.s(chunk) for chunk in chunks)
    body = finalize_file.s(file_id)
    the_chord = chord(header, body)
    the_chord.delay()



@shared_task
def finalize_file(results, file_id):
    valid_cnt = invalid_cnt = 0
    for res in results:
        valid_cnt += res["valid"]
        invalid_cnt += res["invalid"]

    with transaction.atomic():
        ach_file = AchFile.objects.select_for_update().get(id=file_id)
        ach_file.status = AchFile.Status.CHECKED
        ach_file.save(update_fields=["status"])

    logger.info("File validation of %d returns valid=%d, invalid=%d", 
                ach_file.id, valid_cnt, invalid_cnt)

    return file_id


@shared_task
def check_entries(ids):
    summary = evaluate_entries(ids)
    logger.info("checked %d entries: %s", len(ids), summary)
    return summary


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
        chain(process_file.s(str(path)), check_file.s()).delay()
    return len(claimed)
