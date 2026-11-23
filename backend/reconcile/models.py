
from django.db import models


class Location(models.Model):
    location_id = models.CharField(max_length=20, primary_key=True)
    org_id = models.CharField(max_length=20)
    location_name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.location_id} - {self.org_id}"


class SystemARecord(models.Model):
    record_id = models.CharField(max_length=100, db_index=True)

    source_row_number = models.PositiveIntegerField(
        unique=True,
        null=True,
        blank=True
    )

    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    raw_location_id = models.CharField(max_length=100, blank=True)
    event_date = models.CharField(max_length=100, blank=True)
    category_code = models.CharField(max_length=100, blank=True)
    actor_id = models.CharField(max_length=100, blank=True)
    base_value = models.CharField(max_length=100, blank=True)
    adjustment = models.CharField(max_length=100, blank=True)
    total_value = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.record_id


class SystemBEntry(models.Model):
    entry_id = models.CharField(max_length=100, db_index=True)

    source_row_number = models.PositiveIntegerField(
        unique=True,
        null=True,
        blank=True
    )

    record_ref = models.CharField(max_length=100, blank=True)
    normalized_ref = models.CharField(
        max_length=100,
        blank=True,
        db_index=True
    )

    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    raw_location_id = models.CharField(max_length=100, blank=True)
    recorded_on = models.CharField(max_length=100, blank=True)
    value = models.CharField(max_length=100, blank=True)
    label = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.entry_id


class Disagreement(models.Model):
    reason = models.CharField(max_length=50, db_index=True)

    tenant_org_id = models.CharField(
        max_length=20,
        db_index=True,
        blank=True
    )

    normalized_ref = models.CharField(
        max_length=100,
        blank=True,
        db_index=True
    )

    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    system_a_values = models.JSONField(default=dict, blank=True)
    system_b_values = models.JSONField(default=dict, blank=True)

    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.normalized_ref} - {self.reason}"
