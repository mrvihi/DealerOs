from rest_framework import serializers

from .models import Disagreement


class DisagreementSerializer(serializers.ModelSerializer):

    class Meta:
        model = Disagreement
        fields = [
            "id",
            "reason",
            "tenant_org_id",
            "normalized_ref",
            "location",
            "system_a_values",
            "system_b_values",
            "description",
            "created_at",
        ]