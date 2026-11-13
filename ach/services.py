import hashlib
from datetime import datetime
from pathlib import Path

from django.db import transaction

from .models import AchFile, Batch, Entry
from .nacha.parser import parse_file


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def yymmdd(s):
    return datetime.strptime(s, "%y%m%d").date()


def ingest_file(path):
    digest = sha256_of(path)
    header, batches = parse_file(path)

    with transaction.atomic():
        ach_file = AchFile.objects.create(
            file_name=Path(path).name,
            sha256=digest,
            immediate_destination=header["immediate_dest"],
            immediate_origin=header["immediate_origin"],
            destination_name=header["destination_bank"],
            origin_name=header["origin_company"],
            creation_date=yymmdd(header["create_date"]),
            creation_time=header["create_time"],
            id_modifier=header["id_modifier"],
        )

        for b in batches:
            h = b["header"]
            batch = Batch.objects.create(
                ach_file=ach_file,
                batch_number=int(h["batch_number"]),
                service_class=h["service_class"],
                company_name=h["company_name"],
                company_id=h["company_id"],
                sec_code=h["sec_code"],
                entry_description=h["entry_description"],
                effective_date=yymmdd(h["effective_date"]),
                originating_dfi=h["originating_dfi"],
            )

            rows = []
            for e in b["entries"]:
                rows.append(
                    Entry(
                        batch=batch,
                        transaction_code=e["transaction_code"],
                        routing_number=e["routing_number"] + e["check_digit"],
                        account_number=e["account_number"],
                        amount_cents=int(e["amount"]),
                        individual_id=e["individual_id"],
                        individual_name=e["individual_name"],
                        trace_number=e["trace_number"],
                        addenda_type=e.get("addenda_type", ""),
                        addenda_info=e.get("addenda_info", ""),
                    )
                )

            Entry.objects.bulk_create(rows)

    return ach_file
