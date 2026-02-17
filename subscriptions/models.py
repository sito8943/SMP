from datetime import timedelta
from decimal import Decimal
from uuid import uuid4

from django.conf import settings
from django.db import models

from .currency import convert_to_base


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
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="billing_cycles",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    interval = models.PositiveIntegerField(help_text="Number of units between renewals.")
    unit = models.CharField(max_length=16, choices=BillingCycleUnit.choices)

    class Meta:
        ordering = ["interval", "unit"]
        unique_together = ("owner", "interval", "unit")

    def __str__(self) -> str:
        return f"Every {self.interval} {self.unit}"

    def monthly_multiplier(self) -> Decimal:
        interval = Decimal(self.interval)
        mapping = {
            BillingCycleUnit.DAYS: Decimal("30") / interval,
            BillingCycleUnit.WEEKS: Decimal("4.33") / interval,
            BillingCycleUnit.MONTHS: Decimal("1") / interval,
            BillingCycleUnit.YEARS: Decimal("1") / (interval * Decimal("12")),
        }
        return mapping.get(self.unit, Decimal("1"))

    def annual_multiplier(self) -> Decimal:
        return self.monthly_multiplier() * Decimal("12")

    def next_date(self, from_date):
        if self.unit == BillingCycleUnit.DAYS:
            return from_date + timedelta(days=self.interval)
        if self.unit == BillingCycleUnit.WEEKS:
            return from_date + timedelta(weeks=self.interval)
        if self.unit == BillingCycleUnit.MONTHS:
            return from_date + timedelta(days=self.interval * 30)
        if self.unit == BillingCycleUnit.YEARS:
            return from_date + timedelta(days=self.interval * 365)
        return from_date


class Provider(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="providers",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=100)
    website = models.URLField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Subscription(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="subscriptions",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
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

    def monthly_cost_amount(self) -> Decimal:
        cost = Decimal(self.cost_amount)
        return cost * self.billing_cycle.monthly_multiplier()

    def annual_cost_amount(self) -> Decimal:
        cost = Decimal(self.cost_amount)
        return cost * self.billing_cycle.annual_multiplier()

    def monthly_cost_in_base(self) -> Decimal:
        return convert_to_base(self.monthly_cost_amount(), self.cost_currency)

    def annual_cost_in_base(self) -> Decimal:
        return convert_to_base(self.annual_cost_amount(), self.cost_currency)


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


class SubscriptionHistory(TimeStampedModel):
    class EventType(models.TextChoices):
        CREATED = "created", "Created"
        UPDATED = "updated", "Updated"
        STATUS_CHANGED = "status_changed", "Status changed"

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    subscription = models.ForeignKey(
        Subscription, related_name="history", on_delete=models.CASCADE
    )
    event_type = models.CharField(max_length=32, choices=EventType.choices)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.subscription.name} - {self.get_event_type_display()}"
