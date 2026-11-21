from datetime import datetime, timezone

from django.conf import settings
from django.core.management.base import BaseCommand
from faker import Faker

from ach.fakes.pool import build_pool
from ach.nacha.writer import build_file, next_business_day


class Command(BaseCommand):
    help = "Generate a fake NACHA file into the incoming folder"

    def add_arguments(self, parser):
        parser.add_argument("--entries", type=int, default=3)
        parser.add_argument("--seed", type=int, default=None)

    def handle(self, *args, **options):
        originators, receivers, relationships = build_pool()
        file_fake = Faker("en_US")
        if options["seed"] is not None:
            file_fake.seed_instance(options["seed"])

        orig = next(o for o in originators if o["kind"] == "payroll")
        rels = [r for r in relationships if r["originator"] == orig["id"]][:options["entries"]]
        receivers_by_id = {r["id"]: r for r in receivers}

        created_at = datetime.now(timezone.utc)
        lines = build_file(
                    orig, rels, receivers_by_id, file_fake,
                    created_at=created_at, 
                    effective_date=next_business_day()
                )

        incoming = settings.ACH_INCOMING_DIR
        incoming.mkdir(parents=True, exist_ok=True)
        name = f"gen_{created_at:%Y%m%dT%H%M%S}.ach"
        tmp = incoming / (name + ".tmp")
        tmp.write_text("\n".join(lines) + "\n")
        final = tmp.rename(incoming / name)
        self.stdout.write(self.style.SUCCESS(f"Wrote {final} ({len(rels)} entries)"))
