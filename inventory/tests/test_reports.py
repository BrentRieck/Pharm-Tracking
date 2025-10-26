import datetime

import pytest

from inventory.models import Lot, Medication, Office, OfficeMedication
from inventory.services import inventory_summary, lots_expired, lots_expiring_within


@pytest.mark.django_db
def test_lots_expiring_within_filters_by_days():
    office = Office.objects.create(name="Office")
    med = Medication.objects.create(generic_name="Med")
    office_med = OfficeMedication.objects.create(office=office, medication=med)
    Lot.objects.create(
        office_medication=office_med,
        qty=5,
        exp_date=datetime.date.today() + datetime.timedelta(days=10),
    )
    Lot.objects.create(
        office_medication=office_med,
        qty=5,
        exp_date=datetime.date.today() + datetime.timedelta(days=90),
    )

    soon = lots_expiring_within(30, office=office)
    assert soon.count() == 1


@pytest.mark.django_db
def test_lots_expired_includes_past_date():
    office = Office.objects.create(name="Office")
    med = Medication.objects.create(generic_name="Med")
    office_med = OfficeMedication.objects.create(office=office, medication=med)
    Lot.objects.create(
        office_medication=office_med,
        qty=5,
        exp_date=datetime.date.today() - datetime.timedelta(days=1),
    )

    expired = lots_expired(office=office)
    assert expired.count() == 1


@pytest.mark.django_db
def test_inventory_summary_groups_by_office():
    office = Office.objects.create(name="Office")
    med = Medication.objects.create(generic_name="Med")
    office_med = OfficeMedication.objects.create(office=office, medication=med)
    Lot.objects.create(
        office_medication=office_med,
        qty=5,
        exp_date=datetime.date.today() + datetime.timedelta(days=30),
    )
    summary = inventory_summary()
    assert office.name in summary
    assert summary[office.name][0]["total_qty"] == 5
