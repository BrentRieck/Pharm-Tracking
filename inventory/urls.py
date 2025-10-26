from django.urls import path

from . import views

urlpatterns = [
    path("", views.DashboardView.as_view(), name="dashboard"),
    path("offices/", views.OfficeListView.as_view(), name="offices"),
    path("offices/create/", views.OfficeCreateView.as_view(), name="office-create"),
    path("offices/<int:pk>/edit/", views.OfficeUpdateView.as_view(), name="office-edit"),
    path("offices/<int:pk>/", views.OfficeDetailView.as_view(), name="office-detail"),
    path(
        "offices/<int:pk>/stock/",
        views.OfficeMedicationCreateView.as_view(),
        name="office-medication-create",
    ),
    path(
        "office-medications/<int:pk>/edit/",
        views.OfficeMedicationUpdateView.as_view(),
        name="office-medication-edit",
    ),
    path("offices/<int:pk>/lots/", views.LotCreateView.as_view(), name="lot-create"),
    path("lots/<int:pk>/edit/", views.LotUpdateView.as_view(), name="lot-edit"),
    path(
        "offices/<int:pk>/export/",
        views.OfficeExpirationsExportView.as_view(),
        name="office-expiring-export",
    ),
    path("medications/", views.MedicationListView.as_view(), name="medications"),
    path("medications/create/", views.MedicationCreateView.as_view(), name="medication-create"),
    path("users/", views.UserListView.as_view(), name="users"),
    path("users/create/", views.UserCreateView.as_view(), name="user-create"),
    path("memberships/create/", views.MembershipCreateView.as_view(), name="membership-create"),
    path("reports/", views.ReportsView.as_view(), name="reports"),
]
