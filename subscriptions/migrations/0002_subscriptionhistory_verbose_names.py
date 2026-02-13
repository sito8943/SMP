import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("subscriptions", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="SubscriptionHistory",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                (
                    "event_type",
                    models.CharField(
                        choices=[
                            ("created", "Created"),
                            ("updated", "Updated"),
                            ("status_changed", "Status changed"),
                        ],
                        max_length=32,
                    ),
                ),
                ("description", models.TextField(blank=True)),
                (
                    "subscription",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="history",
                        to="subscriptions.subscription",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.AlterField(
            model_name="renewalevent",
            name="amount_amount",
            field=models.DecimalField(decimal_places=2, max_digits=10, verbose_name="Amount"),
        ),
        migrations.AlterField(
            model_name="renewalevent",
            name="amount_currency",
            field=models.CharField(default="USD", max_length=3, verbose_name="Currency"),
        ),
    ]
