from ach.nacha.layouts import ACH_FIELDS, RECORD_LENGTH
from ach.nacha.parser import parse_file, AchFormatError
from pathlib import Path
FIXTURES = Path(__file__).parent / "fixtures"

def test_layouts_cover_every_character_without_gaps():
    for record_type, fields in ACH_FIELDS.items():
        position = 0
        for name, (start, end) in fields.items():
            assert start == position, f"record {record_type}: gap or overlap before {name}"
            assert end > start, f"record {record_type}: empty field {name}"
            position = end
        assert position == RECORD_LENGTH, f"record {record_type} ends at {position}"
