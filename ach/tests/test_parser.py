from pathlib import Path

import pytest

from ach.nacha.layouts import ACH_FIELDS, RECORD_LENGTH
from ach.nacha.parser import AchFormatError, parse_file
from ach.services import ingest_file
from ach.models import AchFile, Batch, Entry

FIXTURES = Path(__file__).parent / "fixtures"


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

    assert AchFile.objects.count() == 1
