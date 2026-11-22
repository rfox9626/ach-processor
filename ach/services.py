import hashlib
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.db import transaction

from .checks import check_account, check_limit, check_routing
from .models import Account, AchFile, Batch, DailyUsage, Entry
from .nacha.parser import parse_file


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def yymmdd(s):
    return datetime.strptime(s, "%y%m%d").date()


def is_debit(code: str) -> bool:
    return code[1] in "78"


def ingest_file(path):
    digest = sha256_of(path)
    header, batches = parse_file(path)

    batch_cnt = tot_debit = tot_credit = 0

    batch_cnt = len(batches)
    for b in batches:
        tot_debit += sum(
            [int(e["amount"]) for e in b["entries"] if is_debit(e["transaction_code"])]
        )
        tot_credit += sum(
            [int(e["amount"]) for e in b["entries"] if not is_debit(e["transaction_code"])]
        )

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
            batch_count=batch_cnt,
            total_debit_cents=tot_debit,
            total_credit_cents=tot_credit,
            status=AchFile.Status.PARSED,
        )

        for b in batches:
            h = b["header"]
            entries = b["entries"]
            b_debit = sum(int(e["amount"]) for e in entries if is_debit(e["transaction_code"]))
            b_credit = sum(int(e["amount"]) for e in entries if not is_debit(e["transaction_code"]))

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
                entry_count=len(entries),
                total_debit_cents=b_debit,
                total_credit_cents=b_credit,
            )

            rows = []
            for e in b["entries"]:
                rows.append(
                    Entry(
                        ach_file=ach_file,
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


def chunked(ids, size):
    res_list = []
    lsz = len(ids)

    q = 0
    while q < lsz:
        if q + size > lsz:
             stop = lsz
        else:
             stop = q + size

        res_list.append(ids[q:stop])
        q += size

    return res_list


def evaluate_entries(entry_ids: list[int]) -> dict[str, int]:
    """Check PENDING entries in this chunk; returns {"valid": n, "invalid": n}."""
    invalid = valid = 0

    with transaction.atomic():
        entries = list(
            Entry.objects.select_for_update(of=("self",))
            .select_related("batch")
            .filter(id__in=entry_ids, status=Entry.Status.PENDING)
            .order_by("id")
        )

        numbers = {e.account_number for e in entries}

        accounts = {
            (a.routing, a.account_number): a
            for a in Account.objects.filter(
                routing=settings.ACH_BANK_ROUTING,
                account_number__in=numbers,
            )
        }

        for entry in entries:
            account = accounts.get((entry.routing_number, entry.account_number))

            if account is None:
                entry.status = Entry.Status.INVALID
                entry.return_code = "R03"
                invalid += 1
                continue

            usage, created = DailyUsage.objects.select_for_update().get_or_create(
                account_id=account.id,
                date=entry.batch.effective_date,
            )

            current_usage = usage.used_cents
            current_amt = entry.amount_cents

            if is_debit(entry.transaction_code):
                limit_code = check_limit(account, current_usage, current_amt)
            else:
                limit_code = None

            code = check_routing(entry.routing_number) or check_account(account) or limit_code

            if code is None:
                if is_debit(entry.transaction_code):
                    usage.used_cents += current_amt
                    usage.save(update_fields=["used_cents"])

                entry.status = Entry.Status.VALID
                valid += 1
            else:
                entry.status = Entry.Status.INVALID
                entry.return_code = code
                invalid += 1

        Entry.objects.bulk_update(entries, ["status", "return_code"])

    return {"valid": valid, "invalid": invalid}
