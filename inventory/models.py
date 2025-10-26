import json
from datetime import date, datetime, timedelta

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("The email address must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.Role.ADMIN)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        STAFF = "staff", "Staff"

    username = models.CharField(max_length=150, blank=True)
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255, blank=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STAFF)
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self) -> str:
        return self.name or self.email


class Office(TimestampedModel):
    name = models.CharField(max_length=255)
    address = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    def __str__(self) -> str:
        return self.name


class OfficeMembership(TimestampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="memberships")
    office = models.ForeignKey(Office, on_delete=models.CASCADE, related_name="memberships")
    role_override = models.CharField(max_length=20, choices=User.Role.choices, blank=True)

    class Meta:
        unique_together = ("user", "office")

    def __str__(self) -> str:
        return f"{self.user} -> {self.office}"


class Medication(TimestampedModel):
    generic_name = models.CharField(max_length=255)
    ndc = models.CharField(max_length=50, blank=True)
    strength = models.CharField(max_length=100, blank=True)
    form = models.CharField(max_length=100, blank=True)
    default_unit = models.CharField(max_length=50, blank=True)

    class Meta:
        ordering = ["generic_name"]

    def __str__(self) -> str:
        return self.generic_name


class OfficeMedication(TimestampedModel):
    office = models.ForeignKey(Office, on_delete=models.CASCADE, related_name="office_medications")
    medication = models.ForeignKey(Medication, on_delete=models.CASCADE, related_name="office_medications")
    reorder_threshold = models.PositiveIntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ("office", "medication")
        ordering = ["medication__generic_name"]

    def __str__(self) -> str:
        return f"{self.office} - {self.medication}"


class LotQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True, status=Lot.Status.ACTIVE)

    def expiring_within(self, days):
        today = timezone.localdate()
        target = today + timedelta(days=days)
        return self.active().filter(exp_date__range=(today, target))

    def expired(self):
        today = timezone.localdate()
        return self.filter(exp_date__lt=today, is_active=True)


class Lot(TimestampedModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        DISCARDED = "discarded", "Discarded"
        USED_UP = "used_up", "Used Up"

    office_medication = models.ForeignKey(
        OfficeMedication, on_delete=models.CASCADE, related_name="lots"
    )
    lot_number = models.CharField(max_length=100, blank=True)
    qty = models.PositiveIntegerField()
    exp_date = models.DateField()
    received_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    last_audited_at = models.DateTimeField(null=True, blank=True)

    objects = LotQuerySet.as_manager()

    class Meta:
        ordering = ["exp_date"]

    def clean(self):
        super().clean()
        today = timezone.localdate()
        if self.exp_date and self.exp_date < today:
            raise ValidationError({"exp_date": "Expiration date cannot be in the past."})
        if self.qty is not None and self.qty < 0:
            raise ValidationError({"qty": "Quantity cannot be negative."})

    def __str__(self) -> str:
        return f"{self.office_medication} lot {self.lot_number or 'N/A'}"


class AuditLog(models.Model):
    class Action(models.TextChoices):
        CREATE = "create", "Create"
        UPDATE = "update", "Update"
        DELETE = "delete", "Delete"
        IMPORT = "import", "Import"
        EXPORT = "export", "Export"
        LOGIN = "login", "Login"

    actor = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=20, choices=Action.choices)
    entity_type = models.CharField(max_length=100)
    entity_id = models.CharField(max_length=50)
    snapshot_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.action} {self.entity_type}:{self.entity_id}"

    @classmethod
    def log(cls, actor, action, instance, extra=None):
        data = {}
        if instance is not None:
            data = json.loads(json.dumps(instance_to_dict(instance)))
        if extra:
            data.update(extra)
        return cls.objects.create(
            actor=actor,
            action=action,
            entity_type=instance.__class__.__name__ if instance else "system",
            entity_id=str(instance.pk) if instance else "-",
            snapshot_json=data,
        )


def instance_to_dict(instance):
    data = {}
    for field in instance._meta.fields:
        value = getattr(instance, field.name)
        if field.is_relation:
            data[field.name] = value.pk if value else None
        elif isinstance(value, (date, datetime)):
            data[field.name] = value.isoformat()
        else:
            data[field.name] = value if value is not None else ""
    return data
