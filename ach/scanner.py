import uuid
from datetime import UTC, datetime
from pathlib import Path


def claim_ready_files(incoming_dir: Path, processing_dir: Path) -> list[Path]:
    incoming_dir.mkdir(parents=True, exist_ok=True)
    processing_dir.mkdir(parents=True, exist_ok=True)

    files = [f for f in incoming_dir.iterdir() if f.is_file() and f.suffix.lower() == ".ach"]
    claimed = []

    for file in files:
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
        new_fname = f"{stamp}_{uuid.uuid4().hex[:8]}_{file.name}"
        dest_file = processing_dir / new_fname

        try:
            claimed.append(file.rename(dest_file))
        except FileNotFoundError:
            # another scanner claimed it first; skip it
            continue

    return claimed
