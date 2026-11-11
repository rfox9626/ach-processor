from .layouts import ACH_FIELDS, HASH_MODULUS, PADDING_LINE, RECORD_LENGTH


class AchFormatError(Exception):
    def __init__(self, line_no, message):
        super().__init__(f"line {line_no}: {message}")
        self.line_no = line_no


def validate_line(line, index):
    if len(line) != RECORD_LENGTH:
        raise AchFormatError(index, f"length is {len(line)}, expected {RECORD_LENGTH}")

    if line == PADDING_LINE:
        return None

    code = line[0]

    if index == 1 and code != "1":
        raise AchFormatError(index, "first record is not 1")

    if code not in ACH_FIELDS:
        raise AchFormatError(index, f"Unknown record {code}")

    return code


def parse_file(path):
    in_batch = False
    all_batches = []
    totals = {}
    file_totals = {"count": 0, "hash": 0, "debits": 0, "credits": 0}
    file_header = {}
    seen_nine = False
    index = 0

    with open(path) as file:
        for index, line in enumerate(file, start=1):
            line = line.rstrip("\r\n")
            code = validate_line(line, index)

            if code is None:
                continue

            fields = ACH_FIELDS[code]
            entry = {
                name: line[start:end].strip() for name, (start, end) in fields.items()
            }

            if code == "1":
                file_header = entry
            elif code == "5":
                if in_batch:
                    raise AchFormatError(index, "batch is already opened")

                in_batch = True
                totals = {"count": 0, "hash": 0, "debits": 0, "credits": 0}
                batch = {"header": entry, "entries": []}
            elif code == "6":
                if not in_batch:
                    raise AchFormatError(index, "batch is not opened")

                batch["entries"].append(entry)
                val = int(entry["transaction_code"])

                if val % 10 == 7:
                    totals["debits"] += int(entry["amount"])
                elif val % 10 == 2:
                    totals["credits"] += int(entry["amount"])

                totals["count"] += 1
                totals["hash"] += int(entry["routing_number"])

            elif code == "7":
                if not in_batch or not batch["entries"]:
                    raise AchFormatError(index, "addenda with no entry above it")

                prev = batch["entries"][-1]

                if prev["addenda_flag"] != "1":
                    raise AchFormatError(
                        index, "addenda for an entry whose addenda flag is 0"
                    )

                if entry["entry_seq"] != prev["trace_number"][-7:]:
                    raise AchFormatError(
                        index, "addenda sequence doesn't match its entry"
                    )

                prev["addenda_type"] = entry["addenda_type"]
                prev["addenda_info"] = entry["payment_info"]
                totals["count"] += 1

            elif code == "8":
                if not in_batch:
                    raise AchFormatError(index, "batch control with no open batch")

                h = batch["header"]
                if (
                    entry["batch_number"] != h["batch_number"]
                    or entry["service_class"] != h["service_class"]
                ):
                    raise AchFormatError(index, "batch control doesn't match header")

                in_batch = False
                all_batches.append(batch)

                expected = {
                    "count": int(entry["entry_count"]),
                    "hash": int(entry["entry_hash"]),
                    "debits": int(entry["total_debits"]),
                    "credits": int(entry["total_credits"]),
                }

                actual = dict(totals, hash=totals["hash"] % HASH_MODULUS)

                if actual != expected:
                    raise AchFormatError(
                        index,
                        f"batch {entry['batch_number']} totals {actual} != control {expected}",
                    )

                for key in totals:
                    file_totals[key] += totals[key]
            elif code == "9":
                expected_results = {
                    "batches": int(entry["batch_count"]),
                    "count": int(entry["entry_count"]),
                    "hash": int(entry["entry_hash"]),
                    "debits": int(entry["total_debits"]),
                    "credits": int(entry["total_credits"]),
                }

                actual = dict(
                    file_totals,
                    hash=file_totals["hash"] % HASH_MODULUS,
                    batches=len(all_batches),
                )

                if actual != expected_results:
                    raise AchFormatError(
                        index,
                        f"file totals {actual} does not match expected {expected_results}",
                    )

                seen_nine = True

        if not seen_nine:
            raise AchFormatError(index, "file has no file control (9) record")
        elif in_batch:
            raise AchFormatError(
                index, "file ended with a batch still open (missing 8)"
            )
        elif index % 10 != 0:
            raise AchFormatError(index, f"file has {index} lines, not a multiple of 10")

    return file_header, all_batches
