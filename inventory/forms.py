from datetime import date

from django import forms
from django.contrib.auth import get_user_model

from .models import Lot, Medication, Office, OfficeMedication, OfficeMembership

User = get_user_model()


class OfficeForm(forms.ModelForm):
    class Meta:
        model = Office
        fields = ["name", "address", "notes", "is_active"]


class MedicationForm(forms.ModelForm):
    class Meta:
        model = Medication
        fields = ["generic_name", "ndc", "strength", "form", "default_unit", "is_active"]


class OfficeMedicationForm(forms.ModelForm):
    class Meta:
        model = OfficeMedication
        fields = ["office", "medication", "reorder_threshold", "notes", "is_active"]


class LotForm(forms.ModelForm):
    class Meta:
        model = Lot
        fields = [
            "office_medication",
            "lot_number",
            "qty",
            "exp_date",
            "received_date",
            "status",
            "is_active",
        ]
        widgets = {
            "exp_date": forms.DateInput(attrs={"type": "date"}),
            "received_date": forms.DateInput(attrs={"type": "date"}),
        }

    def clean_exp_date(self):
        exp_date = self.cleaned_data.get("exp_date")
        if exp_date and exp_date < date.today():
            raise forms.ValidationError("Expiration date cannot be in the past.")
        return exp_date


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["email", "name", "role", "is_active", "is_staff"]


class MembershipForm(forms.ModelForm):
    class Meta:
        model = OfficeMembership
        fields = ["user", "office", "role_override", "is_active"]
