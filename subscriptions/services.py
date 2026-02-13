from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal
from typing import Iterable

from django.utils import timezone

from .currency import convert_to_base
from .models import RenewalEvent, Subscription


@dataclass
class SubscriptionCostSummary:
    monthly_total: Decimal
    annual_total: Decimal


def summarize_costs(subscriptions: Iterable[Subscription]) -> SubscriptionCostSummary:
    monthly = Decimal("0")
    annual = Decimal("0")
    for subscription in subscriptions:
        monthly += subscription.monthly_cost_in_base()
        annual += subscription.annual_cost_in_base()
    return SubscriptionCostSummary(monthly_total=monthly, annual_total=annual)


def upcoming_renewals(days: int = 30) -> list[RenewalEvent]:
    limit_date = timezone.now() + timedelta(days=days)
    return list(
        RenewalEvent.objects.select_related("subscription").filter(
            is_processed=False,
            renewal_date__lte=limit_date,
        )
        .order_by("renewal_date")[:25]
    )
