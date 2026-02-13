from django.urls import path

from . import views

app_name = "subscriptions"

urlpatterns = [
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("providers/", views.ProviderListView.as_view(), name="provider-list"),
    path("providers/add/", views.ProviderCreateView.as_view(), name="provider-add"),
    path("providers/<uuid:pk>/", views.ProviderDetailView.as_view(), name="provider-detail"),
    path("providers/<uuid:pk>/edit/", views.ProviderUpdateView.as_view(), name="provider-edit"),
    path("providers/<uuid:pk>/delete/", views.ProviderDeleteView.as_view(), name="provider-delete"),
    path("billing-cycles/", views.BillingCycleListView.as_view(), name="billingcycle-list"),
    path("billing-cycles/add/", views.BillingCycleCreateView.as_view(), name="billingcycle-add"),
    path("billing-cycles/<uuid:pk>/edit/", views.BillingCycleUpdateView.as_view(), name="billingcycle-edit"),
    path("billing-cycles/<uuid:pk>/delete/", views.BillingCycleDeleteView.as_view(), name="billingcycle-delete"),
    path("subscriptions/", views.SubscriptionListView.as_view(), name="subscription-list"),
    path("subscriptions/add/", views.SubscriptionCreateView.as_view(), name="subscription-add"),
    path("subscriptions/<uuid:pk>/", views.SubscriptionDetailView.as_view(), name="subscription-detail"),
    path("subscriptions/<uuid:pk>/edit/", views.SubscriptionUpdateView.as_view(), name="subscription-edit"),
    path("subscriptions/<uuid:pk>/delete/", views.SubscriptionDeleteView.as_view(), name="subscription-delete"),
    path("notification-rules/", views.NotificationRuleListView.as_view(), name="notificationrule-list"),
    path("notification-rules/add/", views.NotificationRuleCreateView.as_view(), name="notificationrule-add"),
    path("notification-rules/<uuid:pk>/edit/", views.NotificationRuleUpdateView.as_view(), name="notificationrule-edit"),
    path("notification-rules/<uuid:pk>/delete/", views.NotificationRuleDeleteView.as_view(), name="notificationrule-delete"),
    path("renewal-events/", views.RenewalEventListView.as_view(), name="renewalevent-list"),
    path("renewal-events/add/", views.RenewalEventCreateView.as_view(), name="renewalevent-add"),
    path("renewal-events/<uuid:pk>/edit/", views.RenewalEventUpdateView.as_view(), name="renewalevent-edit"),
    path("renewal-events/<uuid:pk>/delete/", views.RenewalEventDeleteView.as_view(), name="renewalevent-delete"),
]
