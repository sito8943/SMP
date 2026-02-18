from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.test import TestCase
from django.utils import timezone

from ..models import (
    BillingCycle,
    BillingCycleUnit,
    NotificationRule,
    NotificationTiming,
    Provider,
    Subscription,
    SubscriptionStatus,
)


class BillingCycleModelTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user("owner-model", password="safe-pass")
        self.other_owner = get_user_model().objects.create_user("other-model", password="safe-pass")

    def test_unique_together_is_enforced_per_owner_interval_and_unit(self):
        BillingCycle.objects.create(owner=self.owner, interval=1, unit=BillingCycleUnit.MONTHS)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                BillingCycle.objects.create(
                    owner=self.owner,
                    interval=1,
                    unit=BillingCycleUnit.MONTHS,
                )

        BillingCycle.objects.create(
            owner=self.other_owner,
            interval=1,
            unit=BillingCycleUnit.MONTHS,
        )
        self.assertEqual(BillingCycle.objects.count(), 2)

    def test_negative_interval_fails_validation(self):
        cycle = BillingCycle(owner=self.owner, interval=-1, unit=BillingCycleUnit.MONTHS)

        with self.assertRaises(ValidationError):
            cycle.full_clean()

    def test_next_date_handles_each_supported_unit(self):
        base_date = timezone.now()
        days_cycle = BillingCycle(owner=self.owner, interval=2, unit=BillingCycleUnit.DAYS)
        weeks_cycle = BillingCycle(owner=self.owner, interval=2, unit=BillingCycleUnit.WEEKS)
        months_cycle = BillingCycle(owner=self.owner, interval=2, unit=BillingCycleUnit.MONTHS)
        years_cycle = BillingCycle(owner=self.owner, interval=2, unit=BillingCycleUnit.YEARS)

        self.assertEqual(days_cycle.next_date(base_date), base_date + timedelta(days=2))
        self.assertEqual(weeks_cycle.next_date(base_date), base_date + timedelta(weeks=2))
        self.assertEqual(months_cycle.next_date(base_date), base_date + timedelta(days=60))
        self.assertEqual(years_cycle.next_date(base_date), base_date + timedelta(days=730))


class NotificationRuleModelTests(TestCase):
    def setUp(self):
        owner = get_user_model().objects.create_user("owner-rule", password="safe-pass")
        provider = Provider.objects.create(owner=owner, name="Provider", category="Software")
        cycle = BillingCycle.objects.create(owner=owner, interval=1, unit=BillingCycleUnit.MONTHS)
        self.subscription = Subscription.objects.create(
            owner=owner,
            name="Subscription",
            provider=provider,
            cost_amount=Decimal("10.00"),
            cost_currency="USD",
            billing_cycle=cycle,
            status=SubscriptionStatus.ACTIVE,
            start_date=timezone.now() - timedelta(days=30),
            next_billing_date=timezone.now() + timedelta(days=7),
        )

    def test_unique_together_is_enforced_for_subscription_and_timing(self):
        NotificationRule.objects.create(
            subscription=self.subscription,
            timing=NotificationTiming.ONE_WEEK_BEFORE,
            is_enabled=True,
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                NotificationRule.objects.create(
                    subscription=self.subscription,
                    timing=NotificationTiming.ONE_WEEK_BEFORE,
                    is_enabled=False,
                )


class SubscriptionModelTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user("owner-sub", password="safe-pass")
        self.provider = Provider.objects.create(owner=self.owner, name="Provider", category="Software")
        self.cycle = BillingCycle.objects.create(
            owner=self.owner,
            interval=1,
            unit=BillingCycleUnit.MONTHS,
        )
        self.subscription = Subscription.objects.create(
            owner=self.owner,
            name="Protected Subscription",
            provider=self.provider,
            cost_amount=Decimal("15.00"),
            cost_currency="USD",
            billing_cycle=self.cycle,
            status=SubscriptionStatus.ACTIVE,
            start_date=timezone.now() - timedelta(days=30),
            next_billing_date=timezone.now() + timedelta(days=7),
        )

    def test_provider_delete_is_blocked_when_subscription_exists(self):
        with self.assertRaises(ProtectedError):
            self.provider.delete()

    def test_billing_cycle_delete_is_blocked_when_subscription_exists(self):
        with self.assertRaises(ProtectedError):
            self.cycle.delete()

    def test_monthly_and_annual_cost_amount_respect_billing_cycle_multiplier(self):
        two_month_cycle = BillingCycle.objects.create(
            owner=self.owner,
            interval=2,
            unit=BillingCycleUnit.MONTHS,
        )
        subscription = Subscription.objects.create(
            owner=self.owner,
            name="Two Month Plan",
            provider=self.provider,
            cost_amount=Decimal("30.00"),
            cost_currency="USD",
            billing_cycle=two_month_cycle,
            status=SubscriptionStatus.ACTIVE,
            start_date=timezone.now() - timedelta(days=10),
            next_billing_date=timezone.now() + timedelta(days=50),
        )

        self.assertEqual(subscription.monthly_cost_amount(), Decimal("15.00"))
        self.assertEqual(subscription.annual_cost_amount(), Decimal("180.00"))
