from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import AuditLog, Lot, Medication, Office, OfficeMedication, OfficeMembership, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Role", {"fields": ("role", "name")}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (None, {"fields": ("name", "role")}),
    )
    list_display = ("email", "name", "role", "is_staff", "is_active")
    ordering = ("email",)
    search_fields = ("email", "name")


@admin.register(Office)
class OfficeAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at")
    search_fields = ("name",)
    list_filter = ("is_active",)


@admin.register(OfficeMembership)
class OfficeMembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "office", "role_override", "is_active")
    autocomplete_fields = ("user", "office")


@admin.register(Medication)
class MedicationAdmin(admin.ModelAdmin):
    list_display = ("generic_name", "ndc", "is_active")
    search_fields = ("generic_name", "ndc")
    list_filter = ("is_active",)


@admin.register(OfficeMedication)
class OfficeMedicationAdmin(admin.ModelAdmin):
    list_display = ("office", "medication", "reorder_threshold", "is_active")
    search_fields = ("office__name", "medication__generic_name")
    list_filter = ("office", "is_active")


@admin.register(Lot)
class LotAdmin(admin.ModelAdmin):
    list_display = ("office_medication", "lot_number", "qty", "exp_date", "status", "is_active")
    list_filter = ("status", "office_medication__office")
    autocomplete_fields = ("office_medication",)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("actor", "action", "entity_type", "entity_id", "created_at")
    search_fields = ("entity_type", "entity_id", "actor__email")
    list_filter = ("action", "created_at")
    readonly_fields = ("snapshot_json",)
