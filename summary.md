# Subscription Manager Platform

The Subscription Manager Platform (SMP) is a research-driven subscription manager designed to help people have complete control over recurring subscriptions, such as streaming platforms, domains, software, and memberships. The application allows users to register subscriptions with different billing cycles (monthly, annually, or others), automatically calculate the actual cost per month and per year, manage statuses such as active, paused, or canceled, and generate reminders before each renewal to avoid unexpected charges. It also offers a clear overview of recurring spending, change histories, and support for custom notification rules, facilitating informed financial decision-making and promoting more conscious consumption of digital services.

## Software Engineering

### User stories

1. As a user, I want to register a subscription with its provider, cost, and billing cycle to keep track of my recurring payments.
2. As a user, I want to edit an existing subscription to update price or plan changes.
3. As a user, I want to cancel or pause a subscription to reflect that it is no longer generating charges.
4. As a user, I want to see the status of each subscription (active, paused, canceled) to know which ones are still generating charges.
5. As a user, I want to see the equivalent monthly cost of each subscription to compare services with different billing cycles.
6. As a user, I want to see the total monthly and annual cost of all my active subscriptions to understand their financial impact.
7. As a user, I want to record the renewal date of my subscription so I know when I'll be charged again.
8. As a user, I want to configure how many days before a renewal I'm notified about, to suit my preferences.
9. As a user, I want to list my subscriptions by provider, status, or cost to quickly find information.
10. As a user, I want to see the change history of a subscription to know when it was modified or canceled.

### Functional Requirements

1. The system must allow users to create, modify, pause, and cancel subscriptions.
2. A subscription must have at least the following:
    - Provider
    - Service name
    - Cost
    - Billing cycle
    - Start date
    - Status. *Note: A subscription can only be in a valid status defined by the domain.*

3. The system must automatically calculate:
- Equivalent monthly cost
- Equivalent annual cost

Notes:

*The calculation must respect the configured billing cycle.*

*Only active subscriptions should be included in the totals.*

4. The system must determine the next subscription renewal date.
6. The system must allow configuring notification rules per subscription or globally.
7. The system must record relevant changes to a subscription (creation, update, status change). *Note: The history must be accessible to the user.*

### Non-Functional Requirements

1. The system should respond to common queries in a reasonable timeframe for personal use.
2. The software should allow scaling to multiple users
3. The software should have the ability to handle different currencies and exchange rates.
4. The software should have a responsive interface that adapts to any screen size.
