
import csv
import re
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from reconcile.models import (
    Location,
    SystemARecord,
    SystemBEntry,
)


def clean(value):
    """Convert missing CSV values to empty strings."""
    return "" if value is None else str(value).strip()


def normalize_ref(value):
    """Normalize references such as '1112' and 'REC - 1112'."""
    value = clean(value).upper()
    normalized = re.sub(r"[^A-Z0-9]", "", value)

    if normalized.isdigit():
        normalized = "REC" + normalized

    return normalized


class Command(BaseCommand):
    help = "Import DealerOS CSV files into the database"

    def handle(self, *args, **options):
        data_dir = (
            Path(settings.BASE_DIR).parent
            / "data"
            / "raw"
            / "DealerOS_Assignment_Dataset"
        )

        locations_file = data_dir / "locations.csv"
        system_a_file = data_dir / "system_a.csv"
        system_b_file = data_dir / "system_b.csv"

        for file_path in (
            locations_file,
            system_a_file,
            system_b_file,
        ):
            if not file_path.exists():
                raise CommandError(
                    f"CSV file not found: {file_path}"
                )

        with transaction.atomic():
            location_count = self.import_locations(locations_file)
            system_a_count = self.import_system_a(system_a_file)
            system_b_count = self.import_system_b(system_b_file)

        self.stdout.write(self.style.SUCCESS(
            "DealerOS CSV import completed successfully!"
        ))
        self.stdout.write(f"Locations imported: {location_count}")
        self.stdout.write(f"System A rows imported: {system_a_count}")
        self.stdout.write(f"System B rows imported: {system_b_count}")

    def read_csv(self, file_path):
        with open(
            file_path,
            mode="r",
            encoding="utf-8-sig",
            newline="",
        ) as csv_file:
            reader = csv.DictReader(csv_file)

            if reader.fieldnames is None:
                raise CommandError(
                    f"CSV file has no header: {file_path.name}"
                )

            for row in reader:
                yield row

    def import_locations(self, file_path):
        count = 0

        for row in self.read_csv(file_path):
            location_id = clean(row.get("location_id"))

            if not location_id:
                raise CommandError(
                    "A locations.csv row has a blank location_id."
                )

            Location.objects.update_or_create(
                location_id=location_id,
                defaults={
                    "org_id": clean(row.get("org_id")),
                    "location_name": clean(row.get("location_name")),
                },
            )
            count += 1

        return count

    def import_system_a(self, file_path):
        count = 0

        for row_number, row in enumerate(
            self.read_csv(file_path),
            start=1,
        ):
            raw_location_id = clean(row.get("location_id"))
            location = Location.objects.filter(
                location_id=raw_location_id
            ).first()

            SystemARecord.objects.update_or_create(
                source_row_number=row_number,
                defaults={
                    "record_id": clean(row.get("record_id")),
                    "location": location,
                    "raw_location_id": raw_location_id,
                    "event_date": clean(row.get("event_date")),
                    "category_code": clean(row.get("category_code")),
                    "actor_id": clean(row.get("actor_id")),
                    "base_value": clean(row.get("base_value")),
                    "adjustment": clean(row.get("adjustment")),
                    "total_value": clean(row.get("total_value")),
                    "state": clean(row.get("state")),
                },
            )
            count += 1

        return count

    def import_system_b(self, file_path):
        count = 0

        for row_number, row in enumerate(
            self.read_csv(file_path),
            start=1,
        ):
            raw_location_id = clean(row.get("location_id"))
            raw_record_ref = clean(row.get("record_ref"))

            location = Location.objects.filter(
                location_id=raw_location_id
            ).first()

            SystemBEntry.objects.update_or_create(
                source_row_number=row_number,
                defaults={
                    "entry_id": clean(row.get("entry_id")),
                    "record_ref": raw_record_ref,
                    "normalized_ref": normalize_ref(raw_record_ref),
                    "location": location,
                    "raw_location_id": raw_location_id,
                    "recorded_on": clean(row.get("recorded_on")),
                    "value": clean(row.get("value")),
                    "label": clean(row.get("label")),
                },
            )
            count += 1

        return count
