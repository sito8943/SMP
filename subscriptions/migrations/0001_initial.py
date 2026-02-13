import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="BillingCycle",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("interval", models.PositiveIntegerField(help_text="Number of units between renewals.")),
                ("unit", models.CharField(choices=[("days", "Days"), ("weeks", "Weeks"), ("months", "Months"), ("years", "Years")], max_length=16)),
            ],
            options={
                "ordering": ["interval", "unit"],
                "unique_together": {("interval", "unit")},
            },
        ),
        migrations.CreateModel(
            name="Provider",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                ("category", models.CharField(max_length=100)),
                ("website", models.URLField(blank=True)),
            ],
            options={
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="Subscription",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                ("cost_amount", models.DecimalField(decimal_places=2, max_digits=10)),
                ("cost_currency", models.CharField(default="USD", max_length=3)),
                ("status", models.CharField(choices=[("active", "Active"), ("paused", "Paused"), ("cancelled", "Cancelled")], default="active", max_length=16)),
                ("start_date", models.DateTimeField()),
                ("next_billing_date", models.DateTimeField()),
                ("cancellation_date", models.DateTimeField(blank=True, null=True)),
                ("notes", models.TextField(blank=True)),
                ("billing_cycle", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="subscriptions", to="subscriptions.billingcycle")),
                ("provider", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="subscriptions", to="subscriptions.provider")),
            ],
            options={
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="RenewalEvent",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("renewal_date", models.DateTimeField()),
                ("amount_amount", models.DecimalField(decimal_places=2, max_digits=10)),
                ("amount_currency", models.CharField(default="USD", max_length=3)),
                ("is_processed", models.BooleanField(default=False)),
                ("subscription", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="renewal_events", to="subscriptions.subscription")),
            ],
            options={
                "ordering": ["renewal_date"],
            },
        ),
        migrations.CreateModel(
            name="NotificationRule",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("timing", models.CharField(choices=[("1_day", "1 day before"), ("3_days", "3 days before"), ("1_week", "1 week before"), ("2_weeks", "2 weeks before")], max_length=16)),
                ("is_enabled", models.BooleanField(default=True)),
                ("subscription", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="notification_rules", to="subscriptions.subscription")),
            ],
            options={
                "ordering": ["subscription", "timing"],
                "unique_together": {("subscription", "timing")},
            },
        ),
    ]
