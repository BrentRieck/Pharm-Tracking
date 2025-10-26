from rest_framework import serializers

from .models import Lot, Medication, Office, OfficeMedication


class OfficeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Office
        fields = ["id", "name", "address", "notes", "is_active"]


class MedicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medication
        fields = ["id", "generic_name", "ndc", "strength", "form", "default_unit", "is_active"]


class OfficeMedicationSerializer(serializers.ModelSerializer):
    medication = MedicationSerializer()

    class Meta:
        model = OfficeMedication
        fields = [
            "id",
            "office",
            "medication",
            "reorder_threshold",
            "notes",
            "is_active",
        ]


class LotSerializer(serializers.ModelSerializer):
    medication = serializers.CharField(source="office_medication.medication.generic_name", read_only=True)

    class Meta:
        model = Lot
        fields = [
            "id",
            "office_medication",
            "medication",
            "lot_number",
            "qty",
            "exp_date",
            "received_date",
            "status",
            "is_active",
        ]


class ReportLotSerializer(serializers.ModelSerializer):
    medication = serializers.CharField(source="office_medication.medication.generic_name")
    office = serializers.CharField(source="office_medication.office.name")

    class Meta:
        model = Lot
        fields = ["id", "medication", "office", "qty", "exp_date", "status"]
