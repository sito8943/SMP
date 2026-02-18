from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from ..models import (
    BillingCycle,
    BillingCycleUnit,
    Provider,
    RenewalEvent,
    Subscription,
    SubscriptionStatus,
)
from ..services import summarize_costs, upcoming_renewals


class CostSummaryServiceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="cost-user", password="safe-pass")

    def test_summarize_costs_returns_zero_for_empty_input(self):
        summary = summarize_costs([])

        self.assertEqual(summary.monthly_total, Decimal("0"))
        self.assertEqual(summary.annual_total, Decimal("0"))

    def test_summarize_costs_aggregates_converted_monthly_and_annual_totals(self):
        provider = Provider.objects.create(owner=self.user, name="Provider", category="Software")
        monthly_cycle = BillingCycle.objects.create(
            owner=self.user,
            interval=1,
            unit=BillingCycleUnit.MONTHS,
        )
        yearly_cycle = BillingCycle.objects.create(
            owner=self.user,
            interval=1,
            unit=BillingCycleUnit.YEARS,
        )
        monthly_sub = Subscription.objects.create(
            owner=self.user,
            name="Monthly USD",
            provider=provider,
            cost_amount=Decimal("10.00"),
            cost_currency="USD",
            billing_cycle=monthly_cycle,
            status=SubscriptionStatus.ACTIVE,
            start_date=timezone.now() - timedelta(days=30),
            next_billing_date=timezone.now() + timedelta(days=1),
        )
        yearly_sub = Subscription.objects.create(
            owner=self.user,
            name="Yearly EUR",
            provider=provider,
            cost_amount=Decimal("20.00"),
            cost_currency="EUR",
            billing_cycle=yearly_cycle,
            status=SubscriptionStatus.ACTIVE,
            start_date=timezone.now() - timedelta(days=60),
            next_billing_date=timezone.now() + timedelta(days=5),
        )

        summary = summarize_costs([monthly_sub, yearly_sub])

        self.assertEqual(summary.monthly_total.quantize(Decimal("0.01")), Decimal("11.80"))
        self.assertEqual(summary.annual_total.quantize(Decimal("0.01")), Decimal("141.60"))


class UpcomingRenewalsServiceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="renew-user", password="safe-pass")
        self.other_user = get_user_model().objects.create_user(
            username="other-renew-user",
            password="safe-pass",
        )
        self.admin = get_user_model().objects.create_superuser(
            username="admin-renew-user",
            email="admin@test.local",
            password="safe-pass",
        )

        self.user_provider = Provider.objects.create(
            owner=self.user,
            name="User Provider",
            category="Streaming",
        )
        self.other_provider = Provider.objects.create(
            owner=self.other_user,
            name="Other Provider",
            category="Streaming",
        )
        self.user_cycle = BillingCycle.objects.create(
            owner=self.user,
            interval=1,
            unit=BillingCycleUnit.MONTHS,
        )
        self.other_cycle = BillingCycle.objects.create(
            owner=self.other_user,
            interval=1,
            unit=BillingCycleUnit.MONTHS,
        )

    def _subscription_for(self, owner, provider, cycle, name):
        return Subscription.objects.create(
            owner=owner,
            name=name,
            provider=provider,
            cost_amount=Decimal("9.99"),
            cost_currency="USD",
            billing_cycle=cycle,
            status=SubscriptionStatus.ACTIVE,
            start_date=timezone.now() - timedelta(days=30),
            next_billing_date=timezone.now() + timedelta(days=7),
        )

    def test_upcoming_renewals_filters_by_window_user_and_processed_flag(self):
        fixed_now = timezone.make_aware(datetime(2026, 2, 1, 12, 0, 0))
        user_sub = self._subscription_for(self.user, self.user_provider, self.user_cycle, "User Sub")
        other_sub = self._subscription_for(
            self.other_user,
            self.other_provider,
            self.other_cycle,
            "Other Sub",
        )

        with patch("subscriptions.services.timezone.now", return_value=fixed_now):
            first = RenewalEvent.objects.create(
                subscription=user_sub,
                renewal_date=fixed_now + timedelta(days=1),
                amount_amount=Decimal("9.99"),
                amount_currency="USD",
                is_processed=False,
            )
            second = RenewalEvent.objects.create(
                subscription=user_sub,
                renewal_date=fixed_now + timedelta(days=3),
                amount_amount=Decimal("9.99"),
                amount_currency="USD",
                is_processed=False,
            )
            RenewalEvent.objects.create(
                subscription=user_sub,
                renewal_date=fixed_now + timedelta(days=5),
                amount_amount=Decimal("9.99"),
                amount_currency="USD",
                is_processed=True,
            )
            RenewalEvent.objects.create(
                subscription=user_sub,
                renewal_date=fixed_now + timedelta(days=45),
                amount_amount=Decimal("9.99"),
                amount_currency="USD",
                is_processed=False,
            )
            RenewalEvent.objects.create(
                subscription=other_sub,
                renewal_date=fixed_now + timedelta(days=2),
                amount_amount=Decimal("9.99"),
                amount_currency="USD",
                is_processed=False,
            )

            renewals = upcoming_renewals(days=30, user=self.user)

        self.assertEqual([event.pk for event in renewals], [first.pk, second.pk])

    def test_upcoming_renewals_includes_all_users_for_superuser(self):
        fixed_now = timezone.make_aware(datetime(2026, 2, 1, 12, 0, 0))
        user_sub = self._subscription_for(self.user, self.user_provider, self.user_cycle, "User Sub")
        other_sub = self._subscription_for(
            self.other_user,
            self.other_provider,
            self.other_cycle,
            "Other Sub",
        )

        with patch("subscriptions.services.timezone.now", return_value=fixed_now):
            RenewalEvent.objects.create(
                subscription=user_sub,
                renewal_date=fixed_now + timedelta(days=1),
                amount_amount=Decimal("5.00"),
                amount_currency="USD",
                is_processed=False,
            )
            RenewalEvent.objects.create(
                subscription=other_sub,
                renewal_date=fixed_now + timedelta(days=2),
                amount_amount=Decimal("7.00"),
                amount_currency="USD",
                is_processed=False,
            )

            renewals = upcoming_renewals(days=30, user=self.admin)

        self.assertEqual(len(renewals), 2)

    def test_upcoming_renewals_limits_to_25_results(self):
        fixed_now = timezone.make_aware(datetime(2026, 2, 1, 12, 0, 0))
        user_sub = self._subscription_for(self.user, self.user_provider, self.user_cycle, "User Sub")

        with patch("subscriptions.services.timezone.now", return_value=fixed_now):
            for day in range(1, 31):
                RenewalEvent.objects.create(
                    subscription=user_sub,
                    renewal_date=fixed_now + timedelta(days=day),
                    amount_amount=Decimal("9.99"),
                    amount_currency="USD",
                    is_processed=False,
                )

            renewals = upcoming_renewals(days=60, user=self.user)

        self.assertEqual(len(renewals), 25)
        self.assertLessEqual(renewals[0].renewal_date, renewals[-1].renewal_date)
