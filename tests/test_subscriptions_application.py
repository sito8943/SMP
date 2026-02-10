import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from subscriptions_application import (
    InMemorySubscriptionRepository,
    InMemoryProviderRepository,
    CreateSubscriptionUseCase,
    UpdateSubscriptionCostUseCase,
    PauseSubscriptionUseCase,
    ResumeSubscriptionUseCase,
    CancelSubscriptionUseCase,
    AddNotificationRuleUseCase,
    GetSubscriptionInsightsUseCase,
)
from subscriptions_ddd import (
    Provider,
    SubscriptionStatus,
    NotificationTiming,
    SubscriptionAnalysisService,
)


def _create_provider(repo: InMemoryProviderRepository, name: str, category: str) -> Provider:
    provider = Provider(uuid4(), name, category)
    repo.save(provider)
    return provider


def _create_subscription(
    create_use_case: CreateSubscriptionUseCase,
    provider: Provider,
    *,
    name: str = "Test Service",
    cost_amount: float = 10.0,
    billing_interval: int = 1,
    billing_unit: str = "months",
    next_due_days: int = 10,
):
    """Generate a subscription through the real use case to keep tests representative."""
    start = datetime.now() - timedelta(days=30)
    next_date = datetime.now() + timedelta(days=next_due_days)
    return create_use_case.execute(
        name=name,
        provider_id=provider.id,
        cost_amount=cost_amount,
        currency="USD",
        billing_interval=billing_interval,
        billing_unit=billing_unit,
        start_date=start,
        next_billing_date=next_date,
    )


@pytest.fixture
def subscription_repo():
    return InMemorySubscriptionRepository()


@pytest.fixture
def provider_repo():
    return InMemoryProviderRepository()


@pytest.fixture
def default_provider(provider_repo):
    return _create_provider(provider_repo, "Test Provider", "Testing")


@pytest.fixture
def create_use_case(subscription_repo, provider_repo):
    return CreateSubscriptionUseCase(subscription_repo, provider_repo)


def test_create_subscription_use_case_generates_initial_renewal_event(
    subscription_repo, default_provider, create_use_case
):
    subscription = _create_subscription(create_use_case, default_provider, cost_amount=15.0)

    assert subscription_repo.find_by_id(subscription.id) is subscription
    assert len(subscription.renewal_events) == 1
    assert subscription.renewal_events[0].renewal_date == subscription.next_billing_date


def test_update_subscription_cost_use_case_updates_future_events(
    subscription_repo, default_provider, create_use_case
):
    update_use_case = UpdateSubscriptionCostUseCase(subscription_repo)
    subscription = _create_subscription(create_use_case, default_provider, cost_amount=20.0)

    updated = update_use_case.execute(subscription.id, 25.0)

    assert updated.cost.amount == pytest.approx(25.0)
    for event in updated.renewal_events:
        assert event.amount.amount == pytest.approx(25.0)


def test_pause_resume_cancel_subscription_use_cases_manage_status_transitions(
    subscription_repo, default_provider, create_use_case
):
    pause_use_case = PauseSubscriptionUseCase(subscription_repo)
    resume_use_case = ResumeSubscriptionUseCase(subscription_repo)
    cancel_use_case = CancelSubscriptionUseCase(subscription_repo)
    subscription = _create_subscription(create_use_case, default_provider)

    paused = pause_use_case.execute(subscription.id)
    assert paused.status == SubscriptionStatus.PAUSED

    resumed = resume_use_case.execute(subscription.id)
    assert resumed.status == SubscriptionStatus.ACTIVE

    cancelled = cancel_use_case.execute(subscription.id)
    assert cancelled.status == SubscriptionStatus.CANCELLED
    assert cancelled.cancellation_date is not None
    assert cancelled.renewal_events == []

    with pytest.raises(ValueError):
        pause_use_case.execute(subscription.id)


def test_add_notification_rule_use_case_persists_rule_and_blocks_duplicates(
    subscription_repo, default_provider, create_use_case
):
    add_rule_use_case = AddNotificationRuleUseCase(subscription_repo)
    subscription = _create_subscription(create_use_case, default_provider)

    rule = add_rule_use_case.execute(subscription.id, NotificationTiming.ONE_WEEK_BEFORE)

    assert rule.timing == NotificationTiming.ONE_WEEK_BEFORE
    saved = subscription_repo.find_by_id(subscription.id)
    assert len(saved.notification_rules) == 1

    with pytest.raises(ValueError):
        add_rule_use_case.execute(subscription.id, NotificationTiming.ONE_WEEK_BEFORE)


def test_get_subscription_insights_use_case_returns_expected_metrics(
    subscription_repo, provider_repo, create_use_case
):
    streaming = _create_provider(provider_repo, "StreamFlix", "Streaming")
    software = _create_provider(provider_repo, "DevSuite", "Software")

    _create_subscription(
        create_use_case,
        streaming,
        name="Streaming Prime",
        cost_amount=15.0,
        billing_unit="months",
        next_due_days=7,
    )
    _create_subscription(
        create_use_case,
        software,
        name="DevSuite Pro",
        cost_amount=120.0,
        billing_unit="years",
        next_due_days=20,
    )

    insights_use_case = GetSubscriptionInsightsUseCase(
        subscription_repo, SubscriptionAnalysisService()
    )
    insights = insights_use_case.execute()

    assert insights["total_subscriptions"] == 2
    assert insights["active_subscriptions"] == 2
    assert insights["monthly_total"].amount == pytest.approx(25.0)
    assert insights["annual_total"].amount == pytest.approx(300.0)
    assert insights["category_breakdown"]["Streaming"].amount == pytest.approx(15.0)
    assert insights["category_breakdown"]["Software"].amount == pytest.approx(10.0)
    assert len(insights["upcoming_renewals"]) == 2
    assert (
        insights["upcoming_renewals"][0].renewal_date
        <= insights["upcoming_renewals"][1].renewal_date
    )
