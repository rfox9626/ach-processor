from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError

from ach.nacha.parser import AchFormatError
from ach.services import ingest_file


class Command(BaseCommand):  # the class must be named exactly "Command"
    help = "Load ACH file"  # shown by: manage.py greet --help

    def add_arguments(self, parser):  # parser is an argparse parser
        parser.add_argument("path", help="Path to the ACH file")

    def handle(self, *args, **options):  # the code that runs
        path = options["path"]

        if not Path(path).is_file():
            raise CommandError(f"No such file: {path}")

        try:
            ach_file = ingest_file(path)
            self.stdout.write(self.style.SUCCESS(ach_file))  # green output
        except IntegrityError as e:
            raise CommandError(f"Already loaded: {path}") from e
        except AchFormatError as e:
            raise CommandError(f"Format error encountered in parsing: {path}") from e
