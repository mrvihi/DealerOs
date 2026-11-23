from decimal import Decimal, InvalidOperation

from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import ValidationError

from .models import Disagreement
from .serializers import DisagreementSerializer


class DisagreementListView(ListAPIView):
    serializer_class = DisagreementSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        org_id = self.request.query_params.get("org_id")

        if not org_id:
            raise ValidationError({
                "error": "org_id query parameter is required."
            })

        queryset = Disagreement.objects.filter(
            tenant_org_id=org_id
        )

        reason = self.request.query_params.get("reason")

        if reason:
            queryset = queryset.filter(reason=reason)

        sort = self.request.query_params.get("sort", "asc")

        if sort not in ["asc", "desc"]:
            raise ValidationError({
                "error": "sort must be either asc or desc."
            })

        def get_total_value(disagreement):
            value = disagreement.system_a_values.get("total_value")

            if value is None or value == "":
                return None

            try:
                return Decimal(str(value).replace(",", ""))
            except (InvalidOperation, ValueError):
                return None

        records = list(queryset)

        valued_records = []
        missing_records = []

        for record in records:
            total = get_total_value(record)

            if total is None:
                missing_records.append(record)
            else:
                valued_records.append((total, record))

        valued_records.sort(
            key=lambda item: item[0],
            reverse=(sort == "desc")
        )

        return [
            record for total, record in valued_records
        ] + missing_records