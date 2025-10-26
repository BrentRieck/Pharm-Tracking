import datetime

import pytest
from django.core.exceptions import ValidationError

from inventory.models import Lot, Medication, Office, OfficeMedication


@pytest.mark.django_db
def test_lot_requires_future_expiration():
    office = Office.objects.create(name="Test Office")
    med = Medication.objects.create(generic_name="Test Med")
    office_med = OfficeMedication.objects.create(office=office, medication=med)
    lot = Lot(
        office_medication=office_med,
        qty=10,
        exp_date=datetime.date.today() - datetime.timedelta(days=1),
    )
    with pytest.raises(ValidationError):
        lot.full_clean()


@pytest.mark.django_db
def test_lot_allows_today_expiration():
    office = Office.objects.create(name="Test Office")
    med = Medication.objects.create(generic_name="Test Med")
    office_med = OfficeMedication.objects.create(office=office, medication=med)
    lot = Lot(
        office_medication=office_med,
        qty=10,
        exp_date=datetime.date.today(),
    )
    lot.full_clean()


@pytest.mark.django_db
def test_lot_quantity_positive():
    office = Office.objects.create(name="Test Office")
    med = Medication.objects.create(generic_name="Test Med")
    office_med = OfficeMedication.objects.create(office=office, medication=med)
    lot = Lot(
        office_medication=office_med,
        qty=-1,
        exp_date=datetime.date.today() + datetime.timedelta(days=10),
    )
    with pytest.raises(ValidationError):
        lot.full_clean()
