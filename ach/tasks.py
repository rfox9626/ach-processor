from celery import shared_task
from ach.services import ingest_file
from celery.utils.log import get_task_logger
logger = get_task_logger(__name__)

@shared_task
def process_file(path):
    ach_file = ingest_file(path)
    logger.info("Loaded %s as file %s", path, ach_file.id)
    return ach_file.id
