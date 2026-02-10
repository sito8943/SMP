"""
Subscription Intelligence Research Platform - Application Layer and Repositories
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from subscriptions_ddd import (
    Subscription, Provider, RenewalEvent, NotificationRule,
    Money, BillingCycle, SubscriptionStatus, NotificationTiming,
    SubscriptionAnalysisService, NotificationService
)


# ============================================================================
# REPOSITORY INTERFACES
# ============================================================================

class ISubscriptionRepository(ABC):
    """Repository interface for Subscription aggregate"""
    
    @abstractmethod
    def find_by_id(self, subscription_id: UUID) -> Optional[Subscription]:
        pass
    
    @abstractmethod
    def find_all(self) -> List[Subscription]:
        pass
    
    @abstractmethod
    def find_active(self) -> List[Subscription]:
        pass
    
    @abstractmethod
    def find_by_provider(self, provider_id: UUID) -> List[Subscription]:
        pass
    
    @abstractmethod
    def save(self, subscription: Subscription) -> None:
        pass
    
    @abstractmethod
    def delete(self, subscription_id: UUID) -> None:
        pass


class IProviderRepository(ABC):
    """Repository interface for Provider entity"""
    
    @abstractmethod
    def find_by_id(self, provider_id: UUID) -> Optional[Provider]:
        pass
    
    @abstractmethod
    def find_by_name(self, name: str) -> Optional[Provider]:
        pass
    
    @abstractmethod
    def find_all(self) -> List[Provider]:
        pass
    
    @abstractmethod
    def save(self, provider: Provider) -> None:
        pass


# ============================================================================
# IN-MEMORY REPOSITORY IMPLEMENTATIONS
# ============================================================================

class InMemorySubscriptionRepository(ISubscriptionRepository):
    
    def __init__(self):
        self._subscriptions: dict[UUID, Subscription] = {}
    
    def find_by_id(self, subscription_id: UUID) -> Optional[Subscription]:
        return self._subscriptions.get(subscription_id)
    
    def find_all(self) -> List[Subscription]:
        return list(self._subscriptions.values())
    
    def find_active(self) -> List[Subscription]:
        return [s for s in self._subscriptions.values() if s.is_active()]
    
    def find_by_provider(self, provider_id: UUID) -> List[Subscription]:
        return [
            s for s in self._subscriptions.values()
            if s.provider.id == provider_id
        ]
    
    def save(self, subscription: Subscription) -> None:
        self._subscriptions[subscription.id] = subscription
    
    def delete(self, subscription_id: UUID) -> None:
        if subscription_id in self._subscriptions:
            del self._subscriptions[subscription_id]


class InMemoryProviderRepository(IProviderRepository):
    
    def __init__(self):
        self._providers: dict[UUID, Provider] = {}
    
    def find_by_id(self, provider_id: UUID) -> Optional[Provider]:
        return self._providers.get(provider_id)
    
    def find_by_name(self, name: str) -> Optional[Provider]:
        for provider in self._providers.values():
            if provider.name.lower() == name.lower():
                return provider
        return None
    
    def find_all(self) -> List[Provider]:
        return list(self._providers.values())
    
    def save(self, provider: Provider) -> None:
        self._providers[provider.id] = provider


# ============================================================================
# APPLICATION SERVICES (Use Cases)
# ============================================================================

class CreateSubscriptionUseCase:
    """Application service for creating subscriptions"""
    
    def __init__(
        self,
        subscription_repo: ISubscriptionRepository,
        provider_repo: IProviderRepository
    ):
        self.subscription_repo = subscription_repo
        self.provider_repo = provider_repo
    
    def execute(
        self,
        name: str,
        provider_id: UUID,
        cost_amount: float,
        currency: str,
        billing_interval: int,
        billing_unit: str,
        start_date: datetime,
        next_billing_date: datetime,
        notes: Optional[str] = None
    ) -> Subscription:
        """Create a new subscription"""
        
        # Find provider
        provider = self.provider_repo.find_by_id(provider_id)
        if not provider:
            raise ValueError(f"Provider {provider_id} not found")
        
        # Create subscription
        subscription = Subscription(
            id=UUID(int=0).hex,
            name=name,
            provider=provider,
            cost=Money(cost_amount, currency),
            billing_cycle=BillingCycle(billing_interval, billing_unit),
            status=SubscriptionStatus.ACTIVE,
            start_date=start_date,
            next_billing_date=next_billing_date,
            notes=notes
        )
        
        from uuid import uuid4
        subscription.id = uuid4()
        
        # Generate first renewal event
        subscription._generate_next_renewal_event()
        
        # Persist
        self.subscription_repo.save(subscription)
        
        return subscription


class UpdateSubscriptionCostUseCase:
    """Application service for updating subscription cost"""
    
    def __init__(self, subscription_repo: ISubscriptionRepository):
        self.subscription_repo = subscription_repo
    
    def execute(self, subscription_id: UUID, new_amount: float) -> Subscription:
        """Update subscription cost (price change)"""
        
        # Find subscription
        subscription = self.subscription_repo.find_by_id(subscription_id)
        if not subscription:
            raise ValueError(f"Subscription {subscription_id} not found")
        
        # Update cost (domain handles validation)
        new_cost = Money(new_amount, subscription.cost.currency)
        subscription.update_cost(new_cost)
        
        # Persist
        self.subscription_repo.save(subscription)
        
        return subscription


class PauseSubscriptionUseCase:
    """Application service for pausing subscriptions"""
    
    def __init__(self, subscription_repo: ISubscriptionRepository):
        self.subscription_repo = subscription_repo
    
    def execute(self, subscription_id: UUID) -> Subscription:
        """Pause a subscription"""
        
        # Find subscription
        subscription = self.subscription_repo.find_by_id(subscription_id)
        if not subscription:
            raise ValueError(f"Subscription {subscription_id} not found")
        
        # Pause (domain handles validation)
        subscription.pause()
        
        # Persist
        self.subscription_repo.save(subscription)
        
        return subscription


class ResumeSubscriptionUseCase:
    """Application service for resuming subscriptions"""
    
    def __init__(self, subscription_repo: ISubscriptionRepository):
        self.subscription_repo = subscription_repo
    
    def execute(self, subscription_id: UUID) -> Subscription:
        """Resume a paused subscription"""
        
        # Find subscription
        subscription = self.subscription_repo.find_by_id(subscription_id)
        if not subscription:
            raise ValueError(f"Subscription {subscription_id} not found")
        
        # Resume (domain handles validation)
        subscription.resume()
        
        # Persist
        self.subscription_repo.save(subscription)
        
        return subscription


class CancelSubscriptionUseCase:
    """Application service for cancelling subscriptions"""
    
    def __init__(self, subscription_repo: ISubscriptionRepository):
        self.subscription_repo = subscription_repo
    
    def execute(self, subscription_id: UUID) -> Subscription:
        """Cancel a subscription"""
        
        # Find subscription
        subscription = self.subscription_repo.find_by_id(subscription_id)
        if not subscription:
            raise ValueError(f"Subscription {subscription_id} not found")
        
        # Cancel (domain handles validation)
        subscription.cancel()
        
        # Persist
        self.subscription_repo.save(subscription)
        
        return subscription


class AddNotificationRuleUseCase:
    """Application service for adding notification rules"""
    
    def __init__(self, subscription_repo: ISubscriptionRepository):
        self.subscription_repo = subscription_repo
    
    def execute(
        self,
        subscription_id: UUID,
        timing: NotificationTiming
    ) -> NotificationRule:
        """Add notification rule to subscription"""
        
        # Find subscription
        subscription = self.subscription_repo.find_by_id(subscription_id)
        if not subscription:
            raise ValueError(f"Subscription {subscription_id} not found")
        
        # Add rule (domain handles validation)
        rule = subscription.add_notification_rule(timing)
        
        # Persist
        self.subscription_repo.save(subscription)
        
        return rule


class GetSubscriptionInsightsUseCase:
    """Application service for getting subscription insights"""
    
    def __init__(
        self,
        subscription_repo: ISubscriptionRepository,
        analysis_service: SubscriptionAnalysisService
    ):
        self.subscription_repo = subscription_repo
        self.analysis_service = analysis_service
    
    def execute(self) -> dict:
        """Get comprehensive subscription insights"""
        
        # Get all subscriptions
        all_subs = self.subscription_repo.find_all()
        active_subs = [s for s in all_subs if s.is_active()]
        
        # Calculate costs
        monthly_total = self.analysis_service.calculate_total_monthly_cost(all_subs)
        annual_total = self.analysis_service.calculate_total_annual_cost(all_subs)
        
        # Get breakdown
        breakdown = self.analysis_service.get_cost_breakdown_by_category(all_subs)
        
        # Get upcoming renewals
        upcoming = self.analysis_service.get_upcoming_renewals(all_subs, days=30)
        
        return {
            'total_subscriptions': len(all_subs),
            'active_subscriptions': len(active_subs),
            'monthly_total': monthly_total,
            'annual_total': annual_total,
            'category_breakdown': breakdown,
            'upcoming_renewals': upcoming
        }


# ============================================================================
# DEMO WITH APPLICATION LAYER
# ============================================================================

def demo_with_application_layer():
    """Demonstrate the complete DDD architecture"""
    from uuid import uuid4
    from datetime import timedelta
    
    # Setup repositories
    subscription_repo = InMemorySubscriptionRepository()
    provider_repo = InMemoryProviderRepository()
    
    # Setup services
    analysis_service = SubscriptionAnalysisService()
    
    # Setup use cases
    create_subscription = CreateSubscriptionUseCase(subscription_repo, provider_repo)
    update_cost = UpdateSubscriptionCostUseCase(subscription_repo)
    pause_subscription = PauseSubscriptionUseCase(subscription_repo)
    resume_subscription = ResumeSubscriptionUseCase(subscription_repo)
    cancel_subscription = CancelSubscriptionUseCase(subscription_repo)
    add_notification = AddNotificationRuleUseCase(subscription_repo)
    get_insights = GetSubscriptionInsightsUseCase(subscription_repo, analysis_service)
    
    # Create providers
    netflix = Provider(uuid4(), "Netflix", "Streaming")
    spotify = Provider(uuid4(), "Spotify", "Music")
    github = Provider(uuid4(), "GitHub", "Software")
    
    provider_repo.save(netflix)
    provider_repo.save(spotify)
    provider_repo.save(github)
    
    print("=== Subscription Intelligence Research Platform Demo ===\n")
    
    # USE CASE 1: Create subscriptions
    print("1. Creating subscriptions...")
    
    netflix_sub = create_subscription.execute(
        name="Netflix Premium",
        provider_id=netflix.id,
        cost_amount=15.99,
        currency="USD",
        billing_interval=1,
        billing_unit="months",
        start_date=datetime.now() - timedelta(days=30),
        next_billing_date=datetime.now() + timedelta(days=5)
    )
    print(f"   ✓ {netflix_sub.name}: ${netflix_sub.cost.amount}/month")
    
    spotify_sub = create_subscription.execute(
        name="Spotify Premium",
        provider_id=spotify.id,
        cost_amount=9.99,
        currency="USD",
        billing_interval=1,
        billing_unit="months",
        start_date=datetime.now() - timedelta(days=60),
        next_billing_date=datetime.now() + timedelta(days=10)
    )
    print(f"   ✓ {spotify_sub.name}: ${spotify_sub.cost.amount}/month")
    
    github_sub = create_subscription.execute(
        name="GitHub Pro",
        provider_id=github.id,
        cost_amount=48.00,
        currency="USD",
        billing_interval=1,
        billing_unit="years",
        start_date=datetime.now() - timedelta(days=100),
        next_billing_date=datetime.now() + timedelta(days=265)
    )
    print(f"   ✓ {github_sub.name}: ${github_sub.cost.amount}/year")
    
    # USE CASE 2: Get insights
    print("\n2. Getting subscription insights...")
    insights = get_insights.execute()
    print(f"   Total subscriptions: {insights['total_subscriptions']}")
    print(f"   Active subscriptions: {insights['active_subscriptions']}")
    print(f"   Monthly total: ${insights['monthly_total'].amount:.2f}")
    print(f"   Annual total: ${insights['annual_total'].amount:.2f}")
    
    print("\n   Category breakdown:")
    for category, cost in insights['category_breakdown'].items():
        print(f"     • {category}: ${cost.amount:.2f}/month")
    
    # USE CASE 3: Add notifications
    print("\n3. Setting up notifications...")
    rule = add_notification.execute(
        netflix_sub.id,
        NotificationTiming.THREE_DAYS_BEFORE
    )
    print(f"   ✓ Netflix: Notify {rule.days_before()} days before renewal")
    
    # USE CASE 4: Update cost (price increase)
    print("\n4. Processing price increase...")
    updated = update_cost.execute(netflix_sub.id, 17.99)
    print(f"   ✓ Netflix new cost: ${updated.cost.amount}/month")
    
    # Refresh insights
    insights = get_insights.execute()
    print(f"   New monthly total: ${insights['monthly_total'].amount:.2f}")
    
    # USE CASE 5: Pause subscription
    print("\n5. Pausing Spotify...")
    paused = pause_subscription.execute(spotify_sub.id)
    print(f"   ✓ Status: {paused.status.value}")
    
    insights = get_insights.execute()
    print(f"   New monthly total: ${insights['monthly_total'].amount:.2f}")
    
    # USE CASE 6: Resume subscription
    print("\n6. Resuming Spotify...")
    resumed = resume_subscription.execute(spotify_sub.id)
    print(f"   ✓ Status: {resumed.status.value}")
    print(f"   Next billing: {resumed.next_billing_date.strftime('%Y-%m-%d')}")
    
    # USE CASE 7: Cancel subscription
    print("\n7. Cancelling GitHub subscription...")
    cancelled = cancel_subscription.execute(github_sub.id)
    print(f"   ✓ Status: {cancelled.status.value}")
    print(f"   Cancelled on: {cancelled.cancellation_date.strftime('%Y-%m-%d')}")
    
    # Final insights
    print("\n8. Final summary...")
    insights = get_insights.execute()
    print(f"   Active subscriptions: {insights['active_subscriptions']}")
    print(f"   Monthly total: ${insights['monthly_total'].amount:.2f}")
    print(f"   Annual total: ${insights['annual_total'].amount:.2f}")
    
    print("\n   Upcoming renewals:")
    for event in insights['upcoming_renewals']:
        sub = subscription_repo.find_by_id(event.subscription_id)
        print(f"     • {sub.name}: ${event.amount.amount:.2f} on {event.renewal_date.strftime('%Y-%m-%d')}")
    
    print("\n=== Demo Complete ===")


if __name__ == "__main__":
    demo_with_application_layer()
