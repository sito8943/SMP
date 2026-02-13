from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from ..models import (
    BillingCycle,
    BillingCycleUnit,
    NotificationRule,
    NotificationTiming,
    Provider,
    RenewalEvent,
    Subscription,
    SubscriptionStatus,
)


class LandingPageTests(TestCase):
    def test_anonymous_user_sees_marketing_copy(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Subscription Intelligence Research Platform")
        self.assertContains(response, "Access the console")

    def test_authenticated_user_is_redirected_to_dashboard(self):
        user = get_user_model().objects.create_user(username="tester", password="pass1234")
        self.client.force_login(user)

        response = self.client.get(reverse("home"))

        self.assertRedirects(response, reverse("subscriptions:dashboard"))


class DashboardViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="owner", password="safe-pass")

    def test_requires_login(self):
        response = self.client.get(reverse("subscriptions:dashboard"))

        login_url = reverse("login")
        expected = f"{login_url}?next={reverse('subscriptions:dashboard')}"
        self.assertRedirects(response, expected)

    def test_displays_domain_counts(self):
        provider = Provider.objects.create(name="StreamFlix", category="Streaming")
        cycle = BillingCycle.objects.create(interval=1, unit=BillingCycleUnit.MONTHS)
        subscription = Subscription.objects.create(
            name="Premium",
            provider=provider,
            cost_amount=10,
            cost_currency="USD",
            billing_cycle=cycle,
            status=SubscriptionStatus.ACTIVE,
            start_date=timezone.now() - timedelta(days=30),
            next_billing_date=timezone.now() + timedelta(days=15),
        )
        NotificationRule.objects.create(
            subscription=subscription, timing=NotificationTiming.ONE_WEEK_BEFORE
        )
        RenewalEvent.objects.create(
            subscription=subscription,
            renewal_date=timezone.now() + timedelta(days=15),
            amount_amount=10,
            amount_currency="USD",
        )

        self.client.force_login(self.user)
        response = self.client.get(reverse("subscriptions:dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Providers")
        self.assertEqual(response.context["providers"], 1)
        self.assertEqual(response.context["subscriptions"], 1)
        self.assertEqual(response.context["billing_cycles"], 1)
        self.assertEqual(response.context["notifications"], 1)
        self.assertEqual(response.context["renewals_pending"], 1)


class ProviderCRUDTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("manager", password="pass1234")
        self.client.force_login(self.user)

    def test_create_provider_flow(self):
        response = self.client.post(
            reverse("subscriptions:provider-add"),
            {"name": "DevSuite", "category": "Software", "website": "https://devsuite.test"},
        )

        self.assertRedirects(response, reverse("subscriptions:provider-list"))
        self.assertEqual(Provider.objects.count(), 1)
        provider = Provider.objects.first()
        self.assertEqual(provider.name, "DevSuite")

    def test_provider_list_requires_authentication(self):
        self.client.logout()
        response = self.client.get(reverse("subscriptions:provider-list"))
        login_url = reverse("login")
        expected = f"{login_url}?next={reverse('subscriptions:provider-list')}"
        self.assertRedirects(response, expected)


class SubscriptionFeaturesTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("analyst", password="pass1234")
        self.provider = Provider.objects.create(name="DevSuite", category="Software")
        self.cycle = BillingCycle.objects.create(interval=1, unit=BillingCycleUnit.MONTHS)
        self.subscription = Subscription.objects.create(
            name="DevSuite Pro",
            provider=self.provider,
            cost_amount=100,
            cost_currency="USD",
            billing_cycle=self.cycle,
            status=SubscriptionStatus.ACTIVE,
            start_date=timezone.now() - timedelta(days=30),
            next_billing_date=timezone.now() + timedelta(days=15),
        )
        self.client.force_login(self.user)

    def test_subscription_filters_by_provider(self):
        other = Provider.objects.create(name="StreamIt", category="Streaming")
        Subscription.objects.create(
            name="Stream Basic",
            provider=other,
            cost_amount=9,
            cost_currency="USD",
            billing_cycle=self.cycle,
            status=SubscriptionStatus.ACTIVE,
            start_date=timezone.now(),
            next_billing_date=timezone.now() + timedelta(days=20),
        )

        response = self.client.get(
            reverse("subscriptions:subscription-list"),
            {"provider": str(self.provider.id)},
        )

        self.assertContains(response, "DevSuite Pro")
        self.assertNotContains(response, "Stream Basic")

    def test_pause_resume_actions_record_history(self):
        pause_url = reverse("subscriptions:subscription-pause", args=[self.subscription.pk])
        resume_url = reverse("subscriptions:subscription-resume", args=[self.subscription.pk])

        response = self.client.post(pause_url, follow=True)
        self.subscription.refresh_from_db()
        self.assertEqual(self.subscription.status, SubscriptionStatus.PAUSED)
        self.assertContains(response, "paused")

        response = self.client.post(resume_url, follow=True)
        self.subscription.refresh_from_db()
        self.assertEqual(self.subscription.status, SubscriptionStatus.ACTIVE)
        self.assertContains(response, "resumed")
