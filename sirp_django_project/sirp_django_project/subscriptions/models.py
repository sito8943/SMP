from uuid import uuid4

from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class BillingCycleUnit(models.TextChoices):
    DAYS = "days", "Days"
    WEEKS = "weeks", "Weeks"
    MONTHS = "months", "Months"
    YEARS = "years", "Years"


class SubscriptionStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    PAUSED = "paused", "Paused"
    CANCELLED = "cancelled", "Cancelled"


class NotificationTiming(models.TextChoices):
    ONE_DAY_BEFORE = "1_day", "1 day before"
    THREE_DAYS_BEFORE = "3_days", "3 days before"
    ONE_WEEK_BEFORE = "1_week", "1 week before"
    TWO_WEEKS_BEFORE = "2_weeks", "2 weeks before"


class BillingCycle(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    interval = models.PositiveIntegerField(help_text="Number of units between renewals.")
    unit = models.CharField(max_length=16, choices=BillingCycleUnit.choices)

    class Meta:
        ordering = ["interval", "unit"]
        unique_together = ("interval", "unit")

    def __str__(self) -> str:
        return f"Every {self.interval} {self.unit}"


class Provider(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=100)
    website = models.URLField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Subscription(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=255)
    provider = models.ForeignKey(
        Provider, related_name="subscriptions", on_delete=models.PROTECT
    )
    cost_amount = models.DecimalField(max_digits=10, decimal_places=2)
    cost_currency = models.CharField(max_length=3, default="USD")
    billing_cycle = models.ForeignKey(
        BillingCycle, related_name="subscriptions", on_delete=models.PROTECT
    )
    status = models.CharField(
        max_length=16, choices=SubscriptionStatus.choices, default=SubscriptionStatus.ACTIVE
    )
    start_date = models.DateTimeField()
    next_billing_date = models.DateTimeField()
    cancellation_date = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.provider.name})"


class NotificationRule(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    subscription = models.ForeignKey(
        Subscription, related_name="notification_rules", on_delete=models.CASCADE
    )
    timing = models.CharField(max_length=16, choices=NotificationTiming.choices)
    is_enabled = models.BooleanField(default=True)

    class Meta:
        ordering = ["subscription", "timing"]
        unique_together = ("subscription", "timing")

    def __str__(self) -> str:
        return f"{self.subscription} - {self.get_timing_display()}"


class RenewalEvent(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    subscription = models.ForeignKey(
        Subscription, related_name="renewal_events", on_delete=models.CASCADE
    )
    renewal_date = models.DateTimeField()
    amount_amount = models.DecimalField("Amount", max_digits=10, decimal_places=2)
    amount_currency = models.CharField("Currency", max_length=3, default="USD")
    is_processed = models.BooleanField(default=False)

    class Meta:
        ordering = ["renewal_date"]

    def __str__(self) -> str:
        return f"{self.subscription} on {self.renewal_date:%Y-%m-%d}"
