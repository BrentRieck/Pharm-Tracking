from collections import defaultdict

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.core.management.base import BaseCommand

from ...services import lots_expiring_within


class Command(BaseCommand):
    help = "Send email digests of expiring lots"

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=settings.EXPIRY_DAYS_DEFAULT)

    def handle(self, *args, **options):
        days = options["days"]
        lots = lots_expiring_within(days)
        if not lots.exists():
            self.stdout.write("No expiring lots found")
            return

        grouped = defaultdict(list)
        for lot in lots:
            office = lot.office_medication.office.name
            grouped[office].append(lot)

        lines = [f"Expiring within {days} days:"]
        for office, entries in grouped.items():
            lines.append(f"\nOffice: {office}")
            for lot in entries:
                med = lot.office_medication.medication.generic_name
                lines.append(f" - {med} lot {lot.lot_number or 'N/A'} qty {lot.qty} exp {lot.exp_date}")

        message = "\n".join(lines)
        User = get_user_model()
        recipients = list(
            User.objects.filter(is_active=True)
            .exclude(email="")
            .values_list("email", flat=True)
        )
        if not recipients:
            self.stdout.write("No recipients available")
            return

        send_mail(
            subject=f"Medication lots expiring in {days} days",
            message=message,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@example.com"),
            recipient_list=recipients,
            fail_silently=True,
        )
        self.stdout.write(self.style.SUCCESS(f"Sent digest to {len(recipients)} recipients"))
