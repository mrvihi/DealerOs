
import re
from decimal import Decimal, InvalidOperation

from django.db import transaction

from .models import (
    SystemARecord,
    SystemBEntry,
    Disagreement,
)


def normalize_ref(value):
    """Normalize references into a common format."""
    value = (value or "").strip().upper()
    normalized = re.sub(r"[^A-Z0-9]", "", value)

    if normalized.isdigit():
        normalized = "REC" + normalized

    return normalized


def parse_amount(value):
    """Convert an amount into Decimal safely."""
    value = (value or "").strip().replace(",", "")

    if not value:
        return None

    try:
        return Decimal(value)
    except InvalidOperation:
        return None


def get_system_a_values(record):
    return {
        "record_id": record.record_id,
        "location_id": record.raw_location_id,
        "event_date": record.event_date,
        "category_code": record.category_code,
        "actor_id": record.actor_id,
        "base_value": record.base_value,
        "adjustment": record.adjustment,
        "total_value": record.total_value,
        "state": record.state,
    }


def get_system_b_values(entries):
    return [
        {
            "entry_id": entry.entry_id,
            "record_ref": entry.record_ref,
            "location_id": entry.raw_location_id,
            "recorded_on": entry.recorded_on,
            "value": entry.value,
            "label": entry.label,
        }
        for entry in entries
    ]


def create_disagreement(
    reason,
    normalized_ref,
    tenant_org_id,
    location,
    system_a_values,
    system_b_values,
    description,
):
    if not tenant_org_id:
        return

    Disagreement.objects.create(
        reason=reason,
        tenant_org_id=tenant_org_id,
        normalized_ref=normalized_ref,
        location=location,
        system_a_values=system_a_values,
        system_b_values=system_b_values,
        description=description,
    )


@transaction.atomic
def run_reconciliation():
    """
    Compare System A and System B.

    Existing disagreement results are replaced on each run.
    Imported source records are never deleted.
    """

    Disagreement.objects.all().delete()

    system_a_records = list(
        SystemARecord.objects.select_related("location").all()
    )

    system_b_entries = list(
        SystemBEntry.objects.select_related("location").all()
    )

    a_by_ref = {}

    for record in system_a_records:
        normalized_ref = normalize_ref(record.record_id)

        if normalized_ref:
            a_by_ref.setdefault(normalized_ref, []).append(record)

    b_by_ref = {}

    for entry in system_b_entries:
        normalized_ref = normalize_ref(entry.record_ref)

        if normalized_ref:
            b_by_ref.setdefault(normalized_ref, []).append(entry)

    for normalized_ref, records in a_by_ref.items():

        matching_entries = b_by_ref.get(normalized_ref, [])

        for record in records:

            a_org = (
                record.location.org_id
                if record.location
                else ""
            )

            if not matching_entries:
                if record.state != "VOIDED":
                    create_disagreement(
                        reason="MISSING_IN_SYSTEM_B",
                        normalized_ref=normalized_ref,
                        tenant_org_id=a_org,
                        location=record.location,
                        system_a_values=get_system_a_values(record),
                        system_b_values={},
                        description="System A record has no matching System B entry.",
                    )
                continue

            same_org_entries = []
            foreign_org_entries = {}

            for entry in matching_entries:
                b_org = (
                    entry.location.org_id
                    if entry.location
                    else ""
                )

                if a_org and b_org and a_org == b_org:
                    same_org_entries.append(entry)

                elif a_org and b_org and a_org != b_org:
                    foreign_org_entries.setdefault(
                        b_org, []
                    ).append(entry)

            # Handle cross-organization matches separately.
            for foreign_org, foreign_entries in foreign_org_entries.items():

                create_disagreement(
                    reason="LOCATION_MISMATCH",
                    normalized_ref=normalized_ref,
                    tenant_org_id=a_org,
                    location=record.location,
                    system_a_values=get_system_a_values(record),
                    system_b_values={
                        "redacted": True,
                        "message": "Details belong to another organization.",
                    },
                    description="Matching reference belongs to a different organization.",
                )

                for entry in foreign_entries:
                    create_disagreement(
                        reason="LOCATION_MISMATCH",
                        normalized_ref=normalized_ref,
                        tenant_org_id=foreign_org,
                        location=entry.location,
                        system_a_values={
                            "redacted": True,
                            "message": "Details belong to another organization.",
                        },
                        system_b_values=get_system_b_values([entry]),
                        description="Matching reference belongs to a different organization.",
                    )

            if not same_org_entries:
                continue

            a_values = get_system_a_values(record)
            b_values = get_system_b_values(same_org_entries)

            # A VOIDED record must not be treated as a normal match.
            if record.state == "VOIDED":
                create_disagreement(
                    reason="VOIDED_RECORD_PRESENT_IN_SYSTEM_B",
                    normalized_ref=normalized_ref,
                    tenant_org_id=a_org,
                    location=record.location,
                    system_a_values=a_values,
                    system_b_values=b_values,
                    description="System B contains an entry for a VOIDED System A record.",
                )
                continue

            # Check location differences within the same organization.
            for entry in same_org_entries:
                if entry.raw_location_id != record.raw_location_id:
                    create_disagreement(
                        reason="LOCATION_MISMATCH",
                        normalized_ref=normalized_ref,
                        tenant_org_id=a_org,
                        location=record.location,
                        system_a_values=a_values,
                        system_b_values=get_system_b_values([entry]),
                        description="System A and System B locations differ.",
                    )

            # Check date differences.
            for entry in same_org_entries:
                if (
                    entry.recorded_on
                    and record.event_date
                    and entry.recorded_on != record.event_date
                ):
                    create_disagreement(
                        reason="DATE_MISMATCH",
                        normalized_ref=normalized_ref,
                        tenant_org_id=a_org,
                        location=record.location,
                        system_a_values=a_values,
                        system_b_values=get_system_b_values([entry]),
                        description="System A and System B dates differ.",
                    )

            # Calculate the System B total.
            amounts = [
                parse_amount(entry.value)
                for entry in same_org_entries
            ]

            a_amount = parse_amount(record.total_value)

            all_amounts_valid = all(
                amount is not None for amount in amounts
            )

            # A split is valid if all B entries sum to A's total.
            total_matches = (
                a_amount is not None
                and all_amounts_valid
                and sum(amounts, Decimal("0")) == a_amount
            )

            # Valid splits must never be classified as duplicates.
            if total_matches:
                continue

            # If totals do not match, check for repeated amounts.
            is_duplicate = (
                len(same_org_entries) > 1
                and all_amounts_valid
                and len(set(amounts)) == 1
            )

            if is_duplicate:
                create_disagreement(
                    reason="DUPLICATE_IN_SYSTEM_B",
                    normalized_ref=normalized_ref,
                    tenant_org_id=a_org,
                    location=record.location,
                    system_a_values=a_values,
                    system_b_values=b_values,
                    description="System B contains repeated entries with the same amount.",
                )
                continue

            # All other amount differences are mismatches.
            create_disagreement(
                reason="VALUE_MISMATCH",
                normalized_ref=normalized_ref,
                tenant_org_id=a_org,
                location=record.location,
                system_a_values=a_values,
                system_b_values=b_values,
                description="System A total value does not match the System B entry total.",
            )

    # Find B entries whose normalized reference does not exist in A.
    all_a_refs = set(a_by_ref.keys())

    for entry in system_b_entries:
        normalized_ref = normalize_ref(entry.record_ref)

        if normalized_ref not in all_a_refs:
            b_org = (
                entry.location.org_id
                if entry.location
                else ""
            )

            create_disagreement(
                reason="ORPHAN_IN_SYSTEM_B",
                normalized_ref=normalized_ref,
                tenant_org_id=b_org,
                location=entry.location,
                system_a_values={},
                system_b_values=get_system_b_values([entry]),
                description="System B entry references a record that does not exist in System A.",
            )

    return Disagreement.objects.count()
