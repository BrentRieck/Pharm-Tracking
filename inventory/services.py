from collections import defaultdict
from datetime import timedelta

from django.conf import settings
from django.db.models import Min, Sum
from django.utils import timezone

from .models import Lot, Office


def get_user_offices(user):
    if user.role == user.Role.ADMIN:
        return Office.objects.filter(is_active=True)
    return Office.objects.filter(memberships__user=user, memberships__is_active=True, is_active=True).distinct()


def lots_expiring_within(days, office=None):
    qs = Lot.objects.active()
    if office is not None:
        if isinstance(office, Office):
            qs = qs.filter(office_medication__office=office)
        else:
            qs = qs.filter(office_medication__office__in=office)
    today = timezone.localdate()
    return qs.filter(exp_date__range=(today, today + timedelta(days=days))).select_related(
        "office_medication__office", "office_medication__medication"
    )


def lots_expired(office=None):
    qs = Lot.objects.active()
    if office is not None:
        if isinstance(office, Office):
            qs = qs.filter(office_medication__office=office)
        else:
            qs = qs.filter(office_medication__office__in=office)
    today = timezone.localdate()
    return qs.filter(exp_date__lt=today).select_related(
        "office_medication__office", "office_medication__medication"
    )


def inventory_summary(offices=None):
    qs = Lot.objects.active()
    if offices is not None:
        if isinstance(offices, Office):
            qs = qs.filter(office_medication__office=offices)
        else:
            qs = qs.filter(office_medication__office__in=offices)
    qs = (
        qs.values("office_medication__office__name", "office_medication__medication__generic_name")
        .annotate(total_qty=Sum("qty"), soonest_exp=Min("exp_date"))
        .order_by("office_medication__office__name", "office_medication__medication__generic_name")
    )
    summary = defaultdict(list)
    for row in qs:
        summary[row["office_medication__office__name"]].append(row)
    return summary


def next_expiring_lots(days_list=None, offices=None):
    if days_list is None:
        days_list = [30, 60, 90]
    data = {}
    for days in days_list:
        data[days] = lots_expiring_within(days, office=offices)
    return data


def default_expiry_days():
    return getattr(settings, "EXPIRY_DAYS_DEFAULT", 60)
