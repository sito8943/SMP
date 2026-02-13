from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views import generic

from .models import BillingCycle, NotificationRule, Provider, RenewalEvent, Subscription


class DashboardView(LoginRequiredMixin, generic.TemplateView):
    template_name = "subscriptions/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["providers"] = Provider.objects.count()
        context["subscriptions"] = Subscription.objects.count()
        context["billing_cycles"] = BillingCycle.objects.count()
        context["notifications"] = NotificationRule.objects.count()
        context["renewals_pending"] = RenewalEvent.objects.filter(is_processed=False).count()
        return context


class ProviderListView(LoginRequiredMixin, generic.ListView):
    model = Provider
    template_name = "subscriptions/provider_list.html"


class ProviderDetailView(LoginRequiredMixin, generic.DetailView):
    model = Provider
    template_name = "subscriptions/provider_detail.html"


class ProviderCreateView(LoginRequiredMixin, generic.CreateView):
    model = Provider
    fields = ["name", "category", "website"]
    template_name = "subscriptions/form.html"
    success_url = reverse_lazy("subscriptions:provider-list")


class ProviderUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Provider
    fields = ["name", "category", "website"]
    template_name = "subscriptions/form.html"
    success_url = reverse_lazy("subscriptions:provider-list")


class ProviderDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = Provider
    template_name = "subscriptions/confirm_delete.html"
    success_url = reverse_lazy("subscriptions:provider-list")


class BillingCycleListView(LoginRequiredMixin, generic.ListView):
    model = BillingCycle
    template_name = "subscriptions/billingcycle_list.html"


class BillingCycleCreateView(LoginRequiredMixin, generic.CreateView):
    model = BillingCycle
    fields = ["interval", "unit"]
    template_name = "subscriptions/form.html"
    success_url = reverse_lazy("subscriptions:billingcycle-list")


class BillingCycleUpdateView(BillingCycleCreateView, generic.UpdateView):
    pass


class BillingCycleDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = BillingCycle
    template_name = "subscriptions/confirm_delete.html"
    success_url = reverse_lazy("subscriptions:billingcycle-list")


class SubscriptionListView(LoginRequiredMixin, generic.ListView):
    model = Subscription
    template_name = "subscriptions/subscription_list.html"


class SubscriptionDetailView(LoginRequiredMixin, generic.DetailView):
    model = Subscription
    template_name = "subscriptions/subscription_detail.html"


class SubscriptionCreateView(LoginRequiredMixin, generic.CreateView):
    model = Subscription
    fields = [
        "name",
        "provider",
        "cost_amount",
        "cost_currency",
        "billing_cycle",
        "status",
        "start_date",
        "next_billing_date",
        "cancellation_date",
        "notes",
    ]
    template_name = "subscriptions/form.html"
    success_url = reverse_lazy("subscriptions:subscription-list")


class SubscriptionUpdateView(SubscriptionCreateView, generic.UpdateView):
    pass


class SubscriptionDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = Subscription
    template_name = "subscriptions/confirm_delete.html"
    success_url = reverse_lazy("subscriptions:subscription-list")


class NotificationRuleListView(LoginRequiredMixin, generic.ListView):
    model = NotificationRule
    template_name = "subscriptions/notificationrule_list.html"


class NotificationRuleCreateView(LoginRequiredMixin, generic.CreateView):
    model = NotificationRule
    fields = ["subscription", "timing", "is_enabled"]
    template_name = "subscriptions/form.html"
    success_url = reverse_lazy("subscriptions:notificationrule-list")


class NotificationRuleUpdateView(NotificationRuleCreateView, generic.UpdateView):
    pass


class NotificationRuleDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = NotificationRule
    template_name = "subscriptions/confirm_delete.html"
    success_url = reverse_lazy("subscriptions:notificationrule-list")


class RenewalEventListView(LoginRequiredMixin, generic.ListView):
    model = RenewalEvent
    template_name = "subscriptions/renewalevent_list.html"


class RenewalEventCreateView(LoginRequiredMixin, generic.CreateView):
    model = RenewalEvent
    fields = ["subscription", "renewal_date", "amount_amount", "amount_currency", "is_processed"]
    template_name = "subscriptions/form.html"
    success_url = reverse_lazy("subscriptions:renewalevent-list")


class RenewalEventUpdateView(RenewalEventCreateView, generic.UpdateView):
    pass


class RenewalEventDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = RenewalEvent
    template_name = "subscriptions/confirm_delete.html"
    success_url = reverse_lazy("subscriptions:renewalevent-list")
