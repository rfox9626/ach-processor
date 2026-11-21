from pathlib import Path

import pytest

from ach.models import AchFile
from ach.nacha.layouts import ACH_FIELDS, RECORD_LENGTH
from ach.nacha.parser import AchFormatError, parse_file
from ach.services import ingest_file
from ach.nacha.fields import check_digit

FIXTURES = Path(__file__).parent / "fixtures"

@pytest.mark.parametrize(
    "routing8, expected",
    [
        ("02100002", "1"),
        ("06100015", "9"),
        ("26107142", "5"),
        ("04200001", "3"),
    ],
)

def test_check_digit(routing8, expected):
    assert check_digit(routing8) == expected


def test_check_digit_rejects_wrong_length():
    with pytest.raises(ValueError):
        check_digit("021000021")        # 9 digits: strict=True in zip() makes this fail loudly


def test_layouts_cover_every_character_without_gaps():
    for record_type, fields in ACH_FIELDS.items():
        position = 0
        for name, (start, end) in fields.items():
            assert start == position, f"record {record_type}: gap or overlap before {name}"
            assert end > start, f"record {record_type}: empty field {name}"
            position = end
        assert position == RECORD_LENGTH, f"record {record_type} ends at {position}"


def test_bad_totals_rejected():
    with pytest.raises(AchFormatError):
        parse_file(FIXTURES / "bad_totals.ach")


def test_sample_file_parses():
    file_header, batches = parse_file(FIXTURES / "sample.ach")
    assert file_header["origin_company"] == "ACME PAYROLL INC"
    assert len(batches) == 2
    assert len(batches[0]["entries"]) == 3
    assert len(batches[1]["entries"]) == 2


@pytest.mark.django_db
def test_ingest_sample_file():
    ach_file = ingest_file(FIXTURES / "sample.ach")
    assert ach_file.batches.count() == 2
    assert AchFile.objects.count() == 1
    assert ach_file.status == AchFile.Status.PARSED
    assert ach_file.total_credit_cents == 453_775
    assert ach_file.total_debit_cents == 24_399
    debit_batch = ach_file.batches.get(batch_number=2)
    assert debit_batch.total_debit_cents == 24_399
    assert debit_batch.total_credit_cents == 0
