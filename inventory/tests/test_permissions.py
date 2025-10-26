import pytest
from django.urls import reverse

from inventory.models import Office, OfficeMembership, User


@pytest.mark.django_db
def test_staff_sees_only_assigned_offices(client):
    office1 = Office.objects.create(name="Office A")
    office2 = Office.objects.create(name="Office B")
    staff = User.objects.create_user(email="staff@example.com", password="pass", role=User.Role.STAFF)
    OfficeMembership.objects.create(user=staff, office=office1)
    client.force_login(staff)

    response = client.get(reverse("offices"))
    assert response.status_code == 200
    assert office1.name in response.content.decode()
    assert office2.name not in response.content.decode()


@pytest.mark.django_db
def test_staff_blocked_from_other_office_detail(client):
    office1 = Office.objects.create(name="Office A")
    office2 = Office.objects.create(name="Office B")
    staff = User.objects.create_user(email="staff2@example.com", password="pass", role=User.Role.STAFF)
    OfficeMembership.objects.create(user=staff, office=office1)
    client.force_login(staff)

    response = client.get(reverse("office-detail", args=[office2.pk]))
    assert response.status_code == 302
    assert response.url == reverse("offices")
