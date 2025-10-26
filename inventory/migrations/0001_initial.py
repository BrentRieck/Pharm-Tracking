# Generated manually for initial schema
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import inventory.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="User",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("password", models.CharField(max_length=128, verbose_name="password")),
                ("last_login", models.DateTimeField(blank=True, null=True, verbose_name="last login")),
                (
                    "is_superuser",
                    models.BooleanField(
                        default=False,
                        help_text="Designates that this user has all permissions without explicitly assigning them.",
                        verbose_name="superuser status",
                    ),
                ),
                ("username", models.CharField(blank=True, max_length=150, verbose_name="username")),
                ("first_name", models.CharField(blank=True, max_length=150, verbose_name="first name")),
                ("last_name", models.CharField(blank=True, max_length=150, verbose_name="last name")),
                ("email", models.EmailField(max_length=254, unique=True, verbose_name="email address")),
                (
                    "is_staff",
                    models.BooleanField(
                        default=False,
                        help_text="Designates whether the user can log into this admin site.",
                        verbose_name="staff status",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=True,
                        help_text="Designates whether this user should be treated as active.",
                        verbose_name="active",
                    ),
                ),
                ("date_joined", models.DateTimeField(default=django.utils.timezone.now, verbose_name="date joined")),
                ("name", models.CharField(blank=True, max_length=255)),
                (
                    "role",
                    models.CharField(
                        choices=[("admin", "Admin"), ("staff", "Staff")],
                        default="staff",
                        max_length=20,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "groups",
                    models.ManyToManyField(
                        blank=True,
                        help_text="The groups this user belongs to.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.group",
                        verbose_name="groups",
                    ),
                ),
                (
                    "user_permissions",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Specific permissions for this user.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.permission",
                        verbose_name="user permissions",
                    ),
                ),
            ],
            options={
                "verbose_name": "user",
                "verbose_name_plural": "users",
            },
            managers=[("objects", inventory.models.UserManager())],
        ),
        migrations.CreateModel(
            name="Office",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_active", models.BooleanField(default=True)),
                ("name", models.CharField(max_length=255)),
                ("address", models.TextField(blank=True)),
                ("notes", models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name="Medication",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_active", models.BooleanField(default=True)),
                ("generic_name", models.CharField(max_length=255)),
                ("ndc", models.CharField(blank=True, max_length=50)),
                ("strength", models.CharField(blank=True, max_length=100)),
                ("form", models.CharField(blank=True, max_length=100)),
                ("default_unit", models.CharField(blank=True, max_length=50)),
            ],
            options={
                "ordering": ["generic_name"],
            },
        ),
        migrations.CreateModel(
            name="OfficeMedication",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_active", models.BooleanField(default=True)),
                ("reorder_threshold", models.PositiveIntegerField(blank=True, null=True)),
                ("notes", models.TextField(blank=True)),
                (
                    "medication",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="office_medications", to="inventory.medication"),
                ),
                (
                    "office",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="office_medications", to="inventory.office"),
                ),
            ],
            options={
                "ordering": ["medication__generic_name"],
                "unique_together": {("office", "medication")},
            },
        ),
        migrations.CreateModel(
            name="OfficeMembership",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_active", models.BooleanField(default=True)),
                ("role_override", models.CharField(blank=True, choices=[("admin", "Admin"), ("staff", "Staff")], max_length=20)),
                (
                    "office",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="memberships", to="inventory.office"),
                ),
                (
                    "user",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="memberships", to=settings.AUTH_USER_MODEL),
                ),
            ],
            options={
                "unique_together": {("user", "office")},
            },
        ),
        migrations.CreateModel(
            name="Lot",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_active", models.BooleanField(default=True)),
                ("lot_number", models.CharField(blank=True, max_length=100)),
                ("qty", models.PositiveIntegerField()),
                ("exp_date", models.DateField()),
                ("received_date", models.DateField(blank=True, null=True)),
                (
                    "status",
                    models.CharField(
                        choices=[("active", "Active"), ("discarded", "Discarded"), ("used_up", "Used Up")],
                        default="active",
                        max_length=20,
                    ),
                ),
                ("last_audited_at", models.DateTimeField(blank=True, null=True)),
                (
                    "office_medication",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="lots", to="inventory.officemedication"),
                ),
            ],
            options={
                "ordering": ["exp_date"],
            },
        ),
        migrations.CreateModel(
            name="AuditLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("action", models.CharField(choices=[("create", "Create"), ("update", "Update"), ("delete", "Delete"), ("import", "Import"), ("export", "Export"), ("login", "Login")], max_length=20)),
                ("entity_type", models.CharField(max_length=100)),
                ("entity_id", models.CharField(max_length=50)),
                ("snapshot_json", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "actor",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
    ]
