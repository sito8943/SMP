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
        self.assertContains(response, "Subscription Manager Platform")
        self.assertContains(response, "Create account")

    def test_authenticated_user_is_redirected_to_dashboard(self):
        user = get_user_model().objects.create_user(username="tester", password="pass1234")
        self.client.force_login(user)

        response = self.client.get(reverse("home"))

        self.assertRedirects(response, reverse("subscriptions:dashboard"))


class SignUpFlowTests(TestCase):
    def test_signup_page_renders(self):
        response = self.client.get(reverse("signup"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Create account")

    def test_signup_creates_user_and_logs_in(self):
        payload = {
            "username": "new-user",
            "password1": "Strong-pass-123",
            "password2": "Strong-pass-123",
        }

        response = self.client.post(reverse("signup"), payload, follow=True)

        self.assertRedirects(response, reverse("subscriptions:dashboard"))
        created = get_user_model().objects.get(username="new-user")
        self.assertFalse(created.is_superuser)
        self.assertEqual(str(created.pk), self.client.session.get("_auth_user_id"))

    def test_signup_existing_username_returns_conflict_message(self):
        get_user_model().objects.create_user(
            username="new-user",
            password="Strong-pass-123",
        )
        payload = {
            "username": "new-user",
            "password1": "Strong-pass-123",
            "password2": "Strong-pass-123",
        }

        response = self.client.post(reverse("signup"), payload)

        self.assertEqual(response.status_code, 409)
        self.assertContains(response, "Username already exists.", status_code=409)


class LoginFlowTests(TestCase):
    def test_unknown_user_shows_invalid_credentials_error(self):
        payload = {
            "username": "ghost-user",
            "password": "bad-password",
        }

        response = self.client.post(reverse("login"), payload)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Incorrect credentials.")


class DashboardViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="owner", password="safe-pass")

    def test_requires_login(self):
        response = self.client.get(reverse("subscriptions:dashboard"))

        login_url = reverse("login")
        expected = f"{login_url}?next={reverse('subscriptions:dashboard')}"
        self.assertRedirects(response, expected)

    def test_displays_domain_counts(self):
        provider = Provider.objects.create(
            owner=self.user,
            name="StreamFlix",
            category="Streaming",
        )
        cycle = BillingCycle.objects.create(owner=self.user, interval=1, unit=BillingCycleUnit.MONTHS)
        subscription = Subscription.objects.create(
            owner=self.user,
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

    def test_hides_other_users_data(self):
        other_user = get_user_model().objects.create_user(
            username="other-owner",
            password="safe-pass",
        )
        own_provider = Provider.objects.create(owner=self.user, name="Own", category="Own")
        own_cycle = BillingCycle.objects.create(
            owner=self.user,
            interval=1,
            unit=BillingCycleUnit.MONTHS,
        )
        own_subscription = Subscription.objects.create(
            owner=self.user,
            name="Own sub",
            provider=own_provider,
            cost_amount=19,
            cost_currency="USD",
            billing_cycle=own_cycle,
            status=SubscriptionStatus.ACTIVE,
            start_date=timezone.now() - timedelta(days=10),
            next_billing_date=timezone.now() + timedelta(days=10),
        )
        NotificationRule.objects.create(
            subscription=own_subscription,
            timing=NotificationTiming.ONE_DAY_BEFORE,
        )
        RenewalEvent.objects.create(
            subscription=own_subscription,
            renewal_date=timezone.now() + timedelta(days=10),
            amount_amount=19,
            amount_currency="USD",
        )

        other_provider = Provider.objects.create(
            owner=other_user,
            name="Other",
            category="Other",
        )
        other_cycle = BillingCycle.objects.create(
            owner=other_user,
            interval=2,
            unit=BillingCycleUnit.MONTHS,
        )
        other_subscription = Subscription.objects.create(
            owner=other_user,
            name="Other sub",
            provider=other_provider,
            cost_amount=99,
            cost_currency="USD",
            billing_cycle=other_cycle,
            status=SubscriptionStatus.ACTIVE,
            start_date=timezone.now() - timedelta(days=5),
            next_billing_date=timezone.now() + timedelta(days=5),
        )
        NotificationRule.objects.create(
            subscription=other_subscription,
            timing=NotificationTiming.ONE_WEEK_BEFORE,
        )
        RenewalEvent.objects.create(
            subscription=other_subscription,
            renewal_date=timezone.now() + timedelta(days=5),
            amount_amount=99,
            amount_currency="USD",
        )

        self.client.force_login(self.user)
        response = self.client.get(reverse("subscriptions:dashboard"))

        self.assertEqual(response.context["providers"], 1)
        self.assertEqual(response.context["subscriptions"], 1)
        self.assertEqual(response.context["billing_cycles"], 1)
        self.assertEqual(response.context["notifications"], 1)
        self.assertEqual(response.context["renewals_pending"], 1)


class ProviderCRUDTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("manager", password="pass1234")
        self.client.force_login(self.user)

    def test_create_provider_flow_assigns_owner(self):
        response = self.client.post(
            reverse("subscriptions:provider-add"),
            {"name": "DevSuite", "category": "Software", "website": "https://devsuite.test"},
        )

        self.assertRedirects(response, reverse("subscriptions:provider-list"))
        self.assertEqual(Provider.objects.count(), 1)
        provider = Provider.objects.first()
        self.assertEqual(provider.name, "DevSuite")
        self.assertEqual(provider.owner, self.user)

    def test_provider_list_requires_authentication(self):
        self.client.logout()
        response = self.client.get(reverse("subscriptions:provider-list"))
        login_url = reverse("login")
        expected = f"{login_url}?next={reverse('subscriptions:provider-list')}"
        self.assertRedirects(response, expected)

    def test_provider_list_shows_only_own_records(self):
        Provider.objects.create(owner=self.user, name="Mine", category="Software")
        other_user = get_user_model().objects.create_user("outsider", password="pass1234")
        Provider.objects.create(owner=other_user, name="Theirs", category="Streaming")

        response = self.client.get(reverse("subscriptions:provider-list"))

        self.assertContains(response, "Mine")
        self.assertNotContains(response, "Theirs")


class SubscriptionFeaturesTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("analyst", password="pass1234")
        self.provider = Provider.objects.create(
            owner=self.user,
            name="DevSuite",
            category="Software",
        )
        self.cycle = BillingCycle.objects.create(
            owner=self.user,
            interval=1,
            unit=BillingCycleUnit.MONTHS,
        )
        self.subscription = Subscription.objects.create(
            owner=self.user,
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
        other_provider = Provider.objects.create(
            owner=self.user,
            name="StreamIt",
            category="Streaming",
        )
        Subscription.objects.create(
            owner=self.user,
            name="Stream Basic",
            provider=other_provider,
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

    def test_user_cannot_access_or_edit_others_subscription(self):
        other_user = get_user_model().objects.create_user("auditor", password="pass1234")
        other_provider = Provider.objects.create(
            owner=other_user,
            name="Other Provider",
            category="Streaming",
        )
        other_cycle = BillingCycle.objects.create(
            owner=other_user,
            interval=3,
            unit=BillingCycleUnit.MONTHS,
        )
        other_subscription = Subscription.objects.create(
            owner=other_user,
            name="Other private sub",
            provider=other_provider,
            cost_amount=15,
            cost_currency="USD",
            billing_cycle=other_cycle,
            status=SubscriptionStatus.ACTIVE,
            start_date=timezone.now() - timedelta(days=10),
            next_billing_date=timezone.now() + timedelta(days=20),
        )

        detail_response = self.client.get(
            reverse("subscriptions:subscription-detail", args=[other_subscription.pk])
        )
        pause_response = self.client.post(
            reverse("subscriptions:subscription-pause", args=[other_subscription.pk])
        )

        self.assertEqual(detail_response.status_code, 404)
        self.assertEqual(pause_response.status_code, 404)
