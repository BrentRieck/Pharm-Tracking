from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import api_views

router = DefaultRouter()
router.register("offices", api_views.OfficeViewSet, basename="api-offices")
router.register("medications", api_views.MedicationViewSet, basename="api-medications")

urlpatterns = [
    path("", include(router.urls)),
    path("offices/<int:pk>/stock/", api_views.OfficeMedicationListView.as_view(), name="api-office-stock"),
    path("offices/<int:pk>/lots/", api_views.OfficeLotListView.as_view(), name="api-office-lots"),
    path("reports/expiring/", api_views.ExpiringReportView.as_view(), name="api-report-expiring"),
    path("reports/expired/", api_views.ExpiredReportView.as_view(), name="api-report-expired"),
    path("reports/inventory/", api_views.InventoryReportView.as_view(), name="api-report-inventory"),
]
