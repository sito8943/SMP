# Subscription Intelligence Research Platform (SIRP)

[![Deploy to Koyeb](https://www.koyeb.com/static/images/deploy/button.svg)](https://app.koyeb.com/deploy?name=ci-cd-primer&type=git&repository=sito8943%2Fsirp&branch=main&instance_type=free&regions=fra&instances_min=0&autoscaling_sleep_idle_delay=3900&env%5BDJANGO_ALLOWED_HOSTS%5D=%7B%7B+KOYEB_PUBLIC_DOMAIN+%7D%7D&ports=5000%3Bhttp%3B%2F&hc_protocol%5B5000%5D=tcp&hc_grace_period%5B5000%5D=5&hc_interval%5B5000%5D=30&hc_restart_limit%5B5000%5D=3&hc_timeout%5B5000%5D=5&hc_path%5B5000%5D=%2F&hc_method%5B5000%5D=get)

<img width="2940" height="1912" alt="image" src="https://github.com/user-attachments/assets/d6efec08-9017-43b7-9dd5-156e9be9388d" />

The Subscription Intelligence Research Platform (SIRP) is a research-grade subscription tracking system implemented using **Domain-Driven Design (DDD)**.

## ⚙️ Plain Django Scaffold

A vanilla Django project (no custom functionality) now lives under `sirp_django_project/`.
Run it like any default Django install:

```bash
cd sirp_django_project
python3 manage.py migrate
python3 manage.py runserver
```

## ✅ Current Capabilities

- CRUD console with authentication, landing page, and dashboard summaries.
- Subscription list filters by provider, status, and cost; shows monthly/annual spend aggregates.
- Pause, resume, and cancel actions write to a subscription history timeline.
- Notification rules, renewal events, and billing cycles managed through the UI.
- Basic multi-currency awareness using configurable exchange rates in `settings.py`.

## 📁 Project Structure

```
subscriptions-ddd/
├── subscriptions_ddd.py          # Domain Layer
├── subscriptions_application.py  # Application Layer
└── README.md                     # This documentation
```

## 🏗️ DDD Architecture

### Domain Model

```
Subscription (Aggregate Root)
  ├── provider: Provider
  ├── cost: Money
  ├── billing_cycle: BillingCycle
  ├── status: SubscriptionStatus
  ├── notification_rules: List[NotificationRule]
  └── renewal_events: List[RenewalEvent]

Provider (Entity)
  ├── name: str
  └── category: str

RenewalEvent (Entity)
  ├── renewal_date: datetime
  └── amount: Money
```

## 🎯 DDD Concepts Implemented

### 1. Value Objects
- Money: Monetary amount with currency
- BillingCycle: Billing cycle (interval + unit)

### 2. Entities
- Provider: Service provider
- RenewalEvent: Future renewal event
- NotificationRule: Notification rule

### 3. Aggregates
- Subscription: Manages lifecycle, billing, and renewals

### 4. Domain Services
- SubscriptionAnalysisService: Analysis and calculations
- NotificationService: Notification management

### 5. Repositories
- ISubscriptionRepository, IProviderRepository
- In-memory implementations

### 6. Use Cases
- CreateSubscriptionUseCase
- UpdateSubscriptionCostUseCase
- PauseSubscriptionUseCase
- ResumeSubscriptionUseCase
- CancelSubscriptionUseCase
- AddNotificationRuleUseCase
- GetSubscriptionInsightsUseCase

## 📊 Business Rules

### Subscriptions
- States: ACTIVE, PAUSED, CANCELLED
- Only active subscriptions contribute to expenses
- Billing cycle determines renewal dates
- Cancelled subscriptions generate no financial impact
- Can be paused and resumed
- Price changes update future events

### Billing Cycles
- Units: days, weeks, months, years
- Positive intervals only
- Monthly and annual equivalent cost calculation
- Determine next renewal dates

### Renewal Events
- Automatically generated for active subscriptions
- Contain date and amount
- Marked as processed upon renewal
- Removed when subscription is cancelled

### Notifications
- Configurable per subscription
- Timing options: 1 day, 3 days, 1 week, 2 weeks before
- Only for active subscriptions
- Can be enabled or disabled

### Financial Analysis
- Monthly equivalent cost calculation
- Annual equivalent cost calculation
- Totals by provider category
- Upcoming renewals

## 🚀 Possible Extensions

- Provider API integration
- Email/SMS alerts
- Import from bank statements
- Historical spending charts
- Plan comparison
- Free trial reminders
- Export to Excel/CSV
- Budgets and spending limits
