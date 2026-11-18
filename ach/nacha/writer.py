from datetime import date, datetime, timedelta

from django.conf import settings

from .fields import alpha, num

KIND_RULES = {
    "payroll": {"service_class": "220", "description": "PAYROLL",
                "codes": {"checking": "22", "savings": "32"}},
    "billpay": {"service_class": "225", "description": "UTIL BILL",
                "codes": {"checking": "27"}},
}

SEC_CODE = "PPD"

# Sending bank (the ODFI): the generator plays this bank
ODFI_ROUTING = "042000013"          # 04200001 + check digit 3
ODFI_NAME = "LGE BANK"


def next_business_day(start_date: date | None = None) -> date:
    """Return the next weekday (Mon-Fri) after start_date."""
    current = start_date or date.today()
    next_day = current + timedelta(days=1)

    # weekday(): Monday is 0 ... Friday is 4, Saturday is 5, Sunday is 6
    while next_day.weekday() >= 5:
        next_day += timedelta(days=1)

    return next_day


def file_header(created_at: datetime) -> str:
    file_date = created_at.strftime("%y%m%d") 
    file_time = created_at.strftime("%H%M")
    line = (
            f"101 {settings.ACH_BANK_ROUTING} {ODFI_ROUTING}"
            f"{file_date}{file_time}"
            f"A094101{alpha(settings.ACH_BANK_NAME,23)}{alpha(ODFI_NAME,23)}{alpha('', 8)}"
    )

    assert len(line) == 94, f"file header is {len(line)} chars"
    return line


def batch_header(originator: dict, batch_number: int, effective_date: str) -> str:
    use_kind = KIND_RULES[originator["kind"]]

    line = (
        f"5{use_kind["service_class"]}{alpha(originator["company_name"], 16)}"
        f"{alpha('',20)}{alpha(originator["company_id"],10)}"
        f"{SEC_CODE}{alpha(use_kind["description"], 10)}{alpha('',6)}{effective_date}"
        f"{alpha('',3)}1{ODFI_ROUTING[:8]}{num(batch_number,7)}"
    )

    assert len(line) == 94, f"Batch header is {len(line)} chars"
    return line


def entry(originator: dict, rel: dict, receiver: dict, amount: int, trace_seq: int) -> str:
    code = KIND_RULES[originator["kind"]]["codes"][receiver["kind"]] 

    line = (
        f"6{code}{receiver['routing'][:8]}{receiver['routing'][8]}"
        f"{alpha(receiver["account_number"], 17)}{num(amount, 10)}"
        f"{alpha(rel["individual_id"], 15)}{alpha(receiver["name"], 22)}"
        f"{alpha("", 2)}0{ODFI_ROUTING[:8] + num(trace_seq, 7)}"
    )

    assert len(line) == 94, f"Entry is {len(line)} chars"
    return line


def batch_control(originator: dict, batch_number: int, entry_count: int,
                  entry_hash: int, total_debit: int, total_credit: int) -> str:
    use_kind = KIND_RULES[originator["kind"]]

    line = (
        f"8{use_kind['service_class']}{num(entry_count, 6)}"
        f"{num(entry_hash % 10**10, 10)}{num(total_debit, 12)}"
        f"{num(total_credit, 12)}{alpha(originator['company_id'],10)}"
        f"{alpha('', 19)}{alpha('', 6)}{ODFI_ROUTING[:8]}{num(batch_number,7)}"
    )

    assert len(line) == 94, f"batch control is {len(line)} chars"
    return line


def file_control(batch_count: int, block_count: int, entry_count: int,
                 entry_hash: int, total_debit: int, total_credit: int) -> str:
    line = (
        f"9{num(batch_count, 6)}{num(block_count, 6)}{num(entry_count, 8)}"
        f"{num(entry_hash % 10**10, 10)}{num(total_debit, 12)}"
        f"{num(total_credit, 12)}{alpha('', 39)}"
    )

    assert len(line) == 94, f"file control is {len(line)} chars"
    return line


def build_file(originator, rels, receivers_by_id, fake, *,
               created_at: datetime, effective_date: date) -> list[str]:
    eff = effective_date.strftime("%y%m%d")
    lines = [file_header(created_at), batch_header(originator, 1, eff)]

    total_credit = total_debit = entry_count = entry_hash = 0

    for seq, rel in enumerate(rels, start=1):
        receiver = receivers_by_id[rel["receiver"]] 
        entry_hash += int(receiver["routing"][:8])
        entry_count += 1

        if originator["kind"] == "payroll":
            amount = fake.random_int(50_000, 500_000)
            total_credit += amount
        else:
            amount = fake.random_int(2_000, 40_000)
            total_debit += amount

        lines.append(entry(originator, rel, receiver, amount, seq))

    ctrl_line = batch_control(
        originator, 1, entry_count, entry_hash, 
        total_debit, total_credit
    )

    lines.append(ctrl_line)

    real_lines = len(lines) + 1 
    filler = (-real_lines) % 10
    block_count = (real_lines + filler) // 10

    lines.append(
        file_control(
            1, block_count, entry_count, entry_hash, 
            total_debit, total_credit
        )
    )

    lines += ["9" * 94] * filler
    return lines
