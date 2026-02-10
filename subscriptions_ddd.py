"""
Subscription Intelligence Research Platform - Domain-Driven Design Implementation
Research-grade subscription tracking and management
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4


# ============================================================================
# VALUE OBJECTS
# ============================================================================

@dataclass(frozen=True)
class Money:
    """Value Object representing a monetary amount"""
    amount: float
    currency: str = "USD"
    
    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Amount cannot be negative")
        if not self.currency or len(self.currency) != 3:
            raise ValueError("Currency must be 3-letter code (e.g., USD)")
    
    def __add__(self, other: 'Money') -> 'Money':
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies")
        return Money(self.amount + other.amount, self.currency)
    
    def __mul__(self, factor: float) -> 'Money':
        return Money(self.amount * factor, self.currency)


@dataclass(frozen=True)
class BillingCycle:
    """Value Object representing a billing cycle"""
    interval: int  # Number of units
    unit: str  # "days", "weeks", "months", "years"
    
    def __post_init__(self):
        if self.interval <= 0:
            raise ValueError("Interval must be positive")
        if self.unit not in ["days", "weeks", "months", "years"]:
            raise ValueError("Unit must be days, weeks, months, or years")
    
    def calculate_next_date(self, from_date: datetime) -> datetime:
        """Calculate next billing date from a given date"""
        if self.unit == "days":
            return from_date + timedelta(days=self.interval)
        elif self.unit == "weeks":
            return from_date + timedelta(weeks=self.interval)
        elif self.unit == "months":
            # Approximate months as 30 days for simplicity
            return from_date + timedelta(days=self.interval * 30)
        elif self.unit == "years":
            return from_date + timedelta(days=self.interval * 365)
    
    def to_monthly_equivalent(self) -> float:
        """Convert billing cycle to monthly multiplier"""
        if self.unit == "days":
            return 30.0 / self.interval
        elif self.unit == "weeks":
            return 4.33 / self.interval
        elif self.unit == "months":
            return 1.0 / self.interval
        elif self.unit == "years":
            return 1.0 / (self.interval * 12)
        return 1.0
    
    def to_annual_equivalent(self) -> float:
        """Convert billing cycle to annual multiplier"""
        return self.to_monthly_equivalent() * 12


# ============================================================================
# ENUMS
# ============================================================================

class SubscriptionStatus(Enum):
    """Lifecycle state of a subscription"""
    ACTIVE = "active"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class NotificationTiming(Enum):
    """When to send renewal notifications"""
    ONE_DAY_BEFORE = "1_day"
    THREE_DAYS_BEFORE = "3_days"
    ONE_WEEK_BEFORE = "1_week"
    TWO_WEEKS_BEFORE = "2_weeks"


# ============================================================================
# ENTITIES
# ============================================================================

@dataclass
class Provider:
    """Entity representing a service provider"""
    id: UUID
    name: str
    category: str  # e.g., "Streaming", "Software", "Fitness"
    website: Optional[str] = None
    
    def __eq__(self, other):
        if not isinstance(other, Provider):
            return False
        return self.id == other.id


@dataclass
class RenewalEvent:
    """Entity representing a future renewal charge"""
    id: UUID
    subscription_id: UUID
    renewal_date: datetime
    amount: Money
    is_processed: bool = False
    
    def is_upcoming(self, days: int = 30) -> bool:
        """Check if renewal is within specified days"""
        delta = self.renewal_date - datetime.now()
        return 0 <= delta.days <= days
    
    def __eq__(self, other):
        if not isinstance(other, RenewalEvent):
            return False
        return self.id == other.id


@dataclass
class NotificationRule:
    """Entity representing when to notify about renewals"""
    id: UUID
    timing: NotificationTiming
    is_enabled: bool = True
    
    def days_before(self) -> int:
        """Get number of days before renewal to notify"""
        mapping = {
            NotificationTiming.ONE_DAY_BEFORE: 1,
            NotificationTiming.THREE_DAYS_BEFORE: 3,
            NotificationTiming.ONE_WEEK_BEFORE: 7,
            NotificationTiming.TWO_WEEKS_BEFORE: 14
        }
        return mapping.get(self.timing, 1)
    
    def should_notify(self, renewal_date: datetime) -> bool:
        """Check if notification should be sent"""
        if not self.is_enabled:
            return False
        
        days_until = (renewal_date - datetime.now()).days
        return days_until == self.days_before()
    
    def __eq__(self, other):
        if not isinstance(other, NotificationRule):
            return False
        return self.id == other.id


# ============================================================================
# AGGREGATES
# ============================================================================

@dataclass
class Subscription:
    """
    Aggregate Root representing a subscription.
    Manages lifecycle, billing, and renewal events.
    """
    id: UUID
    name: str
    provider: Provider
    cost: Money
    billing_cycle: BillingCycle
    status: SubscriptionStatus
    start_date: datetime
    next_billing_date: datetime
    notification_rules: List[NotificationRule] = field(default_factory=list)
    renewal_events: List[RenewalEvent] = field(default_factory=list)
    cancellation_date: Optional[datetime] = None
    notes: Optional[str] = None
    
    def is_active(self) -> bool:
        """Check if subscription is active"""
        return self.status == SubscriptionStatus.ACTIVE
    
    def is_paused(self) -> bool:
        """Check if subscription is paused"""
        return self.status == SubscriptionStatus.PAUSED
    
    def is_cancelled(self) -> bool:
        """Check if subscription is cancelled"""
        return self.status == SubscriptionStatus.CANCELLED
    
    def contributes_to_expenses(self) -> bool:
        """Check if subscription contributes to recurring expenses"""
        return self.is_active()
    
    def pause(self) -> None:
        """Pause the subscription"""
        if self.is_cancelled():
            raise ValueError("Cannot pause a cancelled subscription")
        
        if self.is_paused():
            raise ValueError("Subscription is already paused")
        
        self.status = SubscriptionStatus.PAUSED
    
    def resume(self) -> None:
        """Resume a paused subscription"""
        if not self.is_paused():
            raise ValueError("Can only resume paused subscriptions")
        
        self.status = SubscriptionStatus.ACTIVE
        # Recalculate next billing date
        self.next_billing_date = self.billing_cycle.calculate_next_date(datetime.now())
        self._generate_next_renewal_event()
    
    def cancel(self) -> None:
        """Cancel the subscription"""
        if self.is_cancelled():
            raise ValueError("Subscription is already cancelled")
        
        self.status = SubscriptionStatus.CANCELLED
        self.cancellation_date = datetime.now()
        # Clear future renewal events
        self.renewal_events = [e for e in self.renewal_events if e.is_processed]
    
    def update_cost(self, new_cost: Money) -> None:
        """Update subscription cost (price change)"""
        if new_cost.currency != self.cost.currency:
            raise ValueError("Cannot change currency")
        
        self.cost = new_cost
        # Update future renewal events
        for event in self.renewal_events:
            if not event.is_processed:
                event.amount = new_cost
    
    def update_billing_cycle(self, new_cycle: BillingCycle) -> None:
        """Update billing cycle"""
        self.billing_cycle = new_cycle
        # Recalculate next billing date
        self.next_billing_date = new_cycle.calculate_next_date(datetime.now())
        # Regenerate renewal events
        self._regenerate_renewal_events()
    
    def calculate_monthly_cost(self) -> Money:
        """Calculate equivalent monthly cost"""
        if not self.contributes_to_expenses():
            return Money(0, self.cost.currency)
        
        multiplier = self.billing_cycle.to_monthly_equivalent()
        return self.cost * multiplier
    
    def calculate_annual_cost(self) -> Money:
        """Calculate equivalent annual cost"""
        if not self.contributes_to_expenses():
            return Money(0, self.cost.currency)
        
        multiplier = self.billing_cycle.to_annual_equivalent()
        return self.cost * multiplier
    
    def add_notification_rule(self, timing: NotificationTiming) -> NotificationRule:
        """Add a notification rule"""
        # Check if rule already exists
        if any(r.timing == timing for r in self.notification_rules):
            raise ValueError(f"Notification rule for {timing.value} already exists")
        
        rule = NotificationRule(
            id=uuid4(),
            timing=timing,
            is_enabled=True
        )
        
        self.notification_rules.append(rule)
        return rule
    
    def get_pending_notifications(self) -> List[NotificationRule]:
        """Get notification rules that should trigger"""
        if not self.is_active():
            return []
        
        pending = []
        for rule in self.notification_rules:
            if rule.should_notify(self.next_billing_date):
                pending.append(rule)
        
        return pending
    
    def process_renewal(self) -> RenewalEvent:
        """Process the current renewal and schedule next"""
        if not self.is_active():
            raise ValueError("Cannot process renewal for inactive subscription")
        
        # Find current renewal event
        current_event = None
        for event in self.renewal_events:
            if not event.is_processed and event.renewal_date <= datetime.now():
                current_event = event
                break
        
        if current_event:
            current_event.is_processed = True
        
        # Update next billing date
        self.next_billing_date = self.billing_cycle.calculate_next_date(
            self.next_billing_date
        )
        
        # Generate next renewal event
        return self._generate_next_renewal_event()
    
    def _generate_next_renewal_event(self) -> RenewalEvent:
        """Generate the next renewal event"""
        event = RenewalEvent(
            id=uuid4(),
            subscription_id=self.id,
            renewal_date=self.next_billing_date,
            amount=self.cost
        )
        
        self.renewal_events.append(event)
        return event
    
    def _regenerate_renewal_events(self) -> None:
        """Regenerate all future renewal events"""
        # Remove unprocessed events
        self.renewal_events = [e for e in self.renewal_events if e.is_processed]
        # Generate new event
        if self.is_active():
            self._generate_next_renewal_event()


# ============================================================================
# DOMAIN SERVICES
# ============================================================================

class SubscriptionAnalysisService:
    """Domain Service for subscription analysis"""
    
    @staticmethod
    def calculate_total_monthly_cost(subscriptions: List[Subscription]) -> Money:
        """Calculate total monthly cost across all subscriptions"""
        if not subscriptions:
            return Money(0, "USD")
        
        # Assume all in same currency for simplicity
        currency = subscriptions[0].cost.currency
        total = Money(0, currency)
        
        for sub in subscriptions:
            if sub.contributes_to_expenses():
                total = total + sub.calculate_monthly_cost()
        
        return total
    
    @staticmethod
    def calculate_total_annual_cost(subscriptions: List[Subscription]) -> Money:
        """Calculate total annual cost across all subscriptions"""
        if not subscriptions:
            return Money(0, "USD")
        
        currency = subscriptions[0].cost.currency
        total = Money(0, currency)
        
        for sub in subscriptions:
            if sub.contributes_to_expenses():
                total = total + sub.calculate_annual_cost()
        
        return total
    
    @staticmethod
    def get_upcoming_renewals(subscriptions: List[Subscription], 
                              days: int = 30) -> List[RenewalEvent]:
        """Get all upcoming renewals within specified days"""
        upcoming = []
        
        for sub in subscriptions:
            if sub.is_active():
                for event in sub.renewal_events:
                    if not event.is_processed and event.is_upcoming(days):
                        upcoming.append(event)
        
        return sorted(upcoming, key=lambda e: e.renewal_date)
    
    @staticmethod
    def get_subscriptions_by_category(subscriptions: List[Subscription]) -> dict:
        """Group subscriptions by provider category"""
        by_category = {}
        
        for sub in subscriptions:
            category = sub.provider.category
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(sub)
        
        return by_category
    
    @staticmethod
    def get_cost_breakdown_by_category(subscriptions: List[Subscription]) -> dict:
        """Get monthly cost breakdown by category"""
        by_category = SubscriptionAnalysisService.get_subscriptions_by_category(
            subscriptions
        )
        
        breakdown = {}
        for category, subs in by_category.items():
            total = SubscriptionAnalysisService.calculate_total_monthly_cost(subs)
            breakdown[category] = total
        
        return breakdown


class NotificationService:
    """Domain Service for handling notifications"""
    
    @staticmethod
    def get_all_pending_notifications(subscriptions: List[Subscription]) -> dict:
        """Get all pending notifications across subscriptions"""
        pending = {}
        
        for sub in subscriptions:
            rules = sub.get_pending_notifications()
            if rules:
                pending[sub.id] = {
                    'subscription': sub,
                    'rules': rules
                }
        
        return pending


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

def example_usage():
    """Demonstrate the subscription management system"""
    
    # Create providers
    netflix = Provider(
        id=uuid4(),
        name="Netflix",
        category="Streaming",
        website="https://netflix.com"
    )
    
    spotify = Provider(
        id=uuid4(),
        name="Spotify",
        category="Music",
        website="https://spotify.com"
    )
    
    adobe = Provider(
        id=uuid4(),
        name="Adobe Creative Cloud",
        category="Software",
        website="https://adobe.com"
    )
    
    # Create subscriptions
    netflix_sub = Subscription(
        id=uuid4(),
        name="Netflix Premium",
        provider=netflix,
        cost=Money(15.99, "USD"),
        billing_cycle=BillingCycle(1, "months"),
        status=SubscriptionStatus.ACTIVE,
        start_date=datetime.now() - timedelta(days=60),
        next_billing_date=datetime.now() + timedelta(days=5)
    )
    netflix_sub._generate_next_renewal_event()
    
    spotify_sub = Subscription(
        id=uuid4(),
        name="Spotify Premium",
        provider=spotify,
        cost=Money(9.99, "USD"),
        billing_cycle=BillingCycle(1, "months"),
        status=SubscriptionStatus.ACTIVE,
        start_date=datetime.now() - timedelta(days=30),
        next_billing_date=datetime.now() + timedelta(days=15)
    )
    spotify_sub._generate_next_renewal_event()
    
    adobe_sub = Subscription(
        id=uuid4(),
        name="Adobe Photography Plan",
        provider=adobe,
        cost=Money(119.88, "USD"),
        billing_cycle=BillingCycle(1, "years"),
        status=SubscriptionStatus.ACTIVE,
        start_date=datetime.now() - timedelta(days=200),
        next_billing_date=datetime.now() + timedelta(days=165)
    )
    adobe_sub._generate_next_renewal_event()
    
    print("=== Subscription Intelligence Research Platform ===\n")
    
    # Display subscriptions
    print("Active Subscriptions:")
    all_subs = [netflix_sub, spotify_sub, adobe_sub]
    for sub in all_subs:
        print(f"  • {sub.name} ({sub.provider.name})")
        print(f"    Cost: ${sub.cost.amount:.2f}/{sub.billing_cycle.unit}")
        print(f"    Monthly equivalent: ${sub.calculate_monthly_cost().amount:.2f}")
        print(f"    Next billing: {sub.next_billing_date.strftime('%Y-%m-%d')}")
    
    # Calculate total costs
    analysis = SubscriptionAnalysisService()
    monthly_total = analysis.calculate_total_monthly_cost(all_subs)
    annual_total = analysis.calculate_total_annual_cost(all_subs)
    
    print(f"\n💰 Total Monthly Cost: ${monthly_total.amount:.2f}")
    print(f"💰 Total Annual Cost: ${annual_total.amount:.2f}")
    
    # Cost breakdown by category
    breakdown = analysis.get_cost_breakdown_by_category(all_subs)
    print(f"\n📊 Cost by Category:")
    for category, cost in breakdown.items():
        print(f"  {category}: ${cost.amount:.2f}/month")
    
    # Add notification rules
    print(f"\n🔔 Setting up notifications...")
    netflix_sub.add_notification_rule(NotificationTiming.THREE_DAYS_BEFORE)
    print(f"  ✓ Netflix: Notify 3 days before renewal")
    
    spotify_sub.add_notification_rule(NotificationTiming.ONE_WEEK_BEFORE)
    print(f"  ✓ Spotify: Notify 1 week before renewal")
    
    # Get upcoming renewals
    upcoming = analysis.get_upcoming_renewals(all_subs, days=30)
    print(f"\n📅 Upcoming Renewals (30 days):")
    for event in upcoming:
        sub = next(s for s in all_subs if s.id == event.subscription_id)
        print(f"  • {sub.name}: ${event.amount.amount:.2f} on {event.renewal_date.strftime('%Y-%m-%d')}")
    
    # Pause a subscription
    print(f"\n⏸️  Pausing Spotify subscription...")
    spotify_sub.pause()
    print(f"  Status: {spotify_sub.status.value}")
    
    # Recalculate totals (Spotify won't contribute)
    monthly_total = analysis.calculate_total_monthly_cost(all_subs)
    print(f"  New monthly total: ${monthly_total.amount:.2f}")
    
    # Update pricing
    print(f"\n💵 Netflix price increase...")
    netflix_sub.update_cost(Money(17.99, "USD"))
    print(f"  New cost: ${netflix_sub.cost.amount:.2f}")
    print(f"  New monthly total: ${analysis.calculate_total_monthly_cost(all_subs).amount:.2f}")
    
    # Cancel a subscription
    print(f"\n❌ Cancelling Adobe subscription...")
    adobe_sub.cancel()
    print(f"  Status: {adobe_sub.status.value}")
    print(f"  Cancelled on: {adobe_sub.cancellation_date.strftime('%Y-%m-%d')}")
    print(f"  Final monthly total: ${analysis.calculate_total_monthly_cost(all_subs).amount:.2f}")


if __name__ == "__main__":
    example_usage()
