from rest_framework import generics, permissions, viewsets
from rest_framework.response import Response

from .models import Lot, Medication, Office, OfficeMedication
from .serializers import (
    LotSerializer,
    MedicationSerializer,
    OfficeMedicationSerializer,
    OfficeSerializer,
    ReportLotSerializer,
)
from .services import get_user_offices, inventory_summary, lots_expired, lots_expiring_within


class OfficeViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = OfficeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return get_user_offices(self.request.user)


class MedicationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = MedicationSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Medication.objects.filter(is_active=True)


class OfficeMedicationListView(generics.ListAPIView):
    serializer_class = OfficeMedicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        office = generics.get_object_or_404(Office, pk=self.kwargs["pk"], is_active=True)
        offices = get_user_offices(self.request.user)
        if self.request.user.role != self.request.user.Role.ADMIN and not offices.filter(pk=office.pk).exists():
            return OfficeMedication.objects.none()
        return OfficeMedication.objects.filter(office=office, is_active=True).select_related("medication")


class OfficeLotListView(generics.ListAPIView):
    serializer_class = LotSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        office = generics.get_object_or_404(Office, pk=self.kwargs["pk"], is_active=True)
        offices = get_user_offices(self.request.user)
        if self.request.user.role != self.request.user.Role.ADMIN and not offices.filter(pk=office.pk).exists():
            return Lot.objects.none()
        return Lot.objects.filter(office_medication__office=office, is_active=True).select_related(
            "office_medication__medication"
        )


class ExpiringReportView(generics.GenericAPIView):
    serializer_class = ReportLotSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        days = int(request.GET.get("days", 60))
        office_id = request.GET.get("office_id")
        office = None
        offices = get_user_offices(request.user)
        if office_id:
            office = generics.get_object_or_404(Office, pk=office_id, is_active=True)
        if office and request.user.role != request.user.Role.ADMIN and not offices.filter(pk=office.pk).exists():
            office = None
        lots = lots_expiring_within(days, office=office or offices)
        serializer = self.get_serializer(lots, many=True)
        return Response(serializer.data)


class ExpiredReportView(generics.GenericAPIView):
    serializer_class = ReportLotSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        office_id = request.GET.get("office_id")
        office = None
        offices = get_user_offices(request.user)
        if office_id:
            office = generics.get_object_or_404(Office, pk=office_id, is_active=True)
        if office and request.user.role != request.user.Role.ADMIN and not offices.filter(pk=office.pk).exists():
            office = None
        lots = lots_expired(office=office or offices)
        serializer = self.get_serializer(lots, many=True)
        return Response(serializer.data)


class InventoryReportView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        summary = inventory_summary(get_user_offices(request.user))
        return Response({office: rows for office, rows in summary.items()})
