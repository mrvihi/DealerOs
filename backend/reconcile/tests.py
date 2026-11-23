from decimal import Decimal

from django.test import TestCase

from .models import (
    Location,
    SystemARecord,
    SystemBEntry,
    Disagreement,
)
from .services import run_reconciliation


class ReconciliationTests(TestCase):

    def setUp(self):
        self.location = Location.objects.create(
            location_id="LOC-101",
            org_id="ORG-A",
            location_name="Test Location",
        )

    def create_a(self, record_id, total="100.00", state="CONFIRMED"):
        return SystemARecord.objects.create(
            record_id=record_id,
            raw_location_id="LOC-101",
            location=self.location,
            event_date="2026-04-01",
            base_value="80.00",
            adjustment="20.00",
            total_value=total,
            state=state,
        )

    def create_b(self, entry_id, record_ref, value="100.00"):
        return SystemBEntry.objects.create(
            entry_id=entry_id,
            record_ref=record_ref,
            normalized_ref=record_ref,
            raw_location_id="LOC-101",
            location=self.location,
            recorded_on="2026-04-01",
            value=value,
        )

    def get_reasons(self):
        run_reconciliation()
        return list(
            Disagreement.objects.values_list("reason", flat=True)
        )

    def test_missing_in_system_b(self):
        self.create_a("REC-1001")

        reasons = self.get_reasons()

        self.assertIn("MISSING_IN_SYSTEM_B", reasons)

    def test_orphan_in_system_b(self):
        self.create_b("ENTRY-1", "REC-9999")

        reasons = self.get_reasons()

        self.assertIn("ORPHAN_IN_SYSTEM_B", reasons)

    def test_duplicate_in_system_b(self):
        self.create_a("REC-1001", total="100.00")
        self.create_b("ENTRY-1", "REC-1001", "100.00")
        self.create_b("ENTRY-2", "REC-1001", "100.00")

        reasons = self.get_reasons()

        self.assertIn("DUPLICATE_IN_SYSTEM_B", reasons)

    def test_value_mismatch(self):
        self.create_a("REC-1001", total="100.00")
        self.create_b("ENTRY-1", "REC-1001", "90.00")

        reasons = self.get_reasons()

        self.assertIn("VALUE_MISMATCH", reasons)

    def test_valid_split_entries(self):
        self.create_a("REC-1001", total="100.00")
        self.create_b("ENTRY-1", "REC-1001", "50.00")
        self.create_b("ENTRY-2", "REC-1001", "50.00")

        reasons = self.get_reasons()

        self.assertNotIn("DUPLICATE_IN_SYSTEM_B", reasons)
        self.assertNotIn("VALUE_MISMATCH", reasons)

    def test_blank_system_b_value_is_mismatch(self):
        self.create_a("REC-1001", total="100.00")
        self.create_b("ENTRY-1", "REC-1001", "")

        reasons = self.get_reasons()

        self.assertIn("VALUE_MISMATCH", reasons)

    def test_messy_reference_is_normalized(self):
        self.create_a("REC-1112")
        self.create_b("ENTRY-1", "1112", "100.00")

        reasons = self.get_reasons()

        self.assertNotIn("MISSING_IN_SYSTEM_B", reasons)
        self.assertNotIn("ORPHAN_IN_SYSTEM_B", reasons)

    def test_clean_matching_record(self):
        self.create_a("REC-1001", total="100.00")
        self.create_b("ENTRY-1", "REC-1001", "100.00")

        reasons = self.get_reasons()

        self.assertEqual(reasons, [])

    def test_voided_record_is_flagged(self):
        self.create_a(
            "REC-1001",
            total="100.00",
            state="VOIDED",
        )
        self.create_b("ENTRY-1", "REC-1001", "100.00")

        reasons = self.get_reasons()

        self.assertIn(
            "VOIDED_RECORD_PRESENT_IN_SYSTEM_B",
            reasons,
        )

    def test_location_mismatch_between_tenants_is_redacted(self):
        other_location = Location.objects.create(
            location_id="LOC-202",
            org_id="ORG-B",
            location_name="Other Location",
        )

        self.create_a("REC-1001", total="100.00")

        SystemBEntry.objects.create(
            entry_id="ENTRY-1",
            record_ref="REC-1001",
            normalized_ref="REC-1001",
            raw_location_id="LOC-202",
            location=other_location,
            recorded_on="2026-04-01",
            value="100.00",
        )

        run_reconciliation()

        disagreements = Disagreement.objects.filter(
            reason="LOCATION_MISMATCH"
        )

        self.assertEqual(disagreements.count(), 2)

        org_a = disagreements.get(tenant_org_id="ORG-A")
        org_b = disagreements.get(tenant_org_id="ORG-B")

        self.assertTrue(org_a.system_b_values["redacted"])
        self.assertTrue(org_b.system_a_values["redacted"])