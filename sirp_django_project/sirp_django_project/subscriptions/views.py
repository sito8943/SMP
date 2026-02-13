from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View, generic

from .models import (
    BillingCycle,
    NotificationRule,
    Provider,
    RenewalEvent,
    Subscription,
    SubscriptionHistory,
    SubscriptionStatus,
)
from django.conf import settings
from .services import summarize_costs, upcoming_renewals


class LandingPageView(generic.TemplateView):
    template_name = "home.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("subscriptions:dashboard")
        return super().dispatch(request, *args, **kwargs)


class DashboardView(LoginRequiredMixin, generic.TemplateView):
    template_name = "subscriptions/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        subs = Subscription.objects.all()
        active_subs = subs.filter(status=SubscriptionStatus.ACTIVE)
        summary = summarize_costs(active_subs)
        context["providers"] = Provider.objects.count()
        context["subscriptions"] = subs.count()
        context["billing_cycles"] = BillingCycle.objects.count()
        context["notifications"] = NotificationRule.objects.count()
        context["renewals_pending"] = RenewalEvent.objects.filter(is_processed=False).count()
        context["monthly_total"] = summary.monthly_total
        context["annual_total"] = summary.annual_total
        context["upcoming_renewals"] = upcoming_renewals()
        context["base_currency"] = settings.BASE_CURRENCY
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


class ProviderUpdateView(ProviderCreateView, generic.UpdateView):
    pass


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

    def get_queryset(self):
        queryset = super().get_queryset().select_related("provider", "billing_cycle")
        provider = self.request.GET.get("provider")
        status = self.request.GET.get("status")
        cost_min = self.request.GET.get("cost_min")
        cost_max = self.request.GET.get("cost_max")

        if provider:
            queryset = queryset.filter(provider__id=provider)
        if status:
            queryset = queryset.filter(status=status)
        if cost_min:
            queryset = queryset.filter(cost_amount__gte=cost_min)
        if cost_max:
            queryset = queryset.filter(cost_amount__lte=cost_max)
        order = self.request.GET.get("order")
        if order in {"cost_amount", "-cost_amount", "name", "-name"}:
            queryset = queryset.order_by(order)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["providers"] = Provider.objects.all()
        context["selected_provider"] = self.request.GET.get("provider", "")
        context["selected_status"] = self.request.GET.get("status", "")
        context["cost_min"] = self.request.GET.get("cost_min", "")
        context["cost_max"] = self.request.GET.get("cost_max", "")
        context["order"] = self.request.GET.get("order", "")
        return context

class SubscriptionDetailView(LoginRequiredMixin, generic.DetailView):
    model = Subscription
    template_name = "subscriptions/subscription_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        subscription: Subscription = self.object
        context["monthly_cost"] = subscription.monthly_cost_amount()
        context["annual_cost"] = subscription.annual_cost_amount()
        context["monthly_cost_base"] = subscription.monthly_cost_in_base()
        context["annual_cost_base"] = subscription.annual_cost_in_base()
        context["history"] = subscription.history.all()[:20]
        context["base_currency"] = settings.BASE_CURRENCY
        return context


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

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for field_name in ("start_date", "next_billing_date", "cancellation_date"):
            if field_name in form.fields:
                form.fields[field_name].widget.input_type = "date"
        return form

    def form_valid(self, form):
        response = super().form_valid(form)
        SubscriptionHistory.objects.create(
            subscription=self.object,
            event_type=SubscriptionHistory.EventType.CREATED,
            description="Subscription created",
        )
        return response


class SubscriptionUpdateView(SubscriptionCreateView, generic.UpdateView):
    def form_valid(self, form):
        changed = form.changed_data.copy()
        response = super().form_valid(form)
        if changed:
            SubscriptionHistory.objects.create(
                subscription=self.object,
                event_type=SubscriptionHistory.EventType.UPDATED,
                description=f"Updated fields: {', '.join(changed)}",
            )
        return response


class SubscriptionDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = Subscription
    template_name = "subscriptions/confirm_delete.html"
    success_url = reverse_lazy("subscriptions:subscription-list")


class SubscriptionStatusActionView(LoginRequiredMixin, View):
    action_name = ""

    def post(self, request, pk):
        subscription = get_object_or_404(Subscription, pk=pk)
        error = self.perform_action(subscription)
        if error:
            messages.error(request, error)
        else:
            subscription.save()
            SubscriptionHistory.objects.create(
                subscription=subscription,
                event_type=SubscriptionHistory.EventType.STATUS_CHANGED,
                description=f"Subscription {self.action_name}",
            )
            messages.success(request, f"Subscription {subscription.name} {self.action_name}.")
        return redirect("subscriptions:subscription-detail", pk=subscription.pk)

    def perform_action(self, subscription: Subscription) -> str | None:
        return None


class SubscriptionPauseView(SubscriptionStatusActionView):
    action_name = "paused"

    def perform_action(self, subscription: Subscription) -> str | None:
        if subscription.status == SubscriptionStatus.CANCELLED:
            return "Cannot pause a cancelled subscription."
        if subscription.status == SubscriptionStatus.PAUSED:
            return "Subscription is already paused."
        subscription.status = SubscriptionStatus.PAUSED
        return None


class SubscriptionResumeView(SubscriptionStatusActionView):
    action_name = "resumed"

    def perform_action(self, subscription: Subscription) -> str | None:
        if subscription.status != SubscriptionStatus.PAUSED:
            return "Only paused subscriptions can be resumed."
        subscription.status = SubscriptionStatus.ACTIVE
        subscription.next_billing_date = subscription.billing_cycle.next_date(timezone.now())
        return None


class SubscriptionCancelView(SubscriptionStatusActionView):
    action_name = "cancelled"

    def perform_action(self, subscription: Subscription) -> str | None:
        if subscription.status == SubscriptionStatus.CANCELLED:
            return "Subscription already cancelled."
        subscription.status = SubscriptionStatus.CANCELLED
        subscription.cancellation_date = timezone.now()
        subscription.renewal_events.filter(is_processed=False).delete()
        return None


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

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if "renewal_date" in form.fields:
            form.fields["renewal_date"].widget.input_type = "date"
        return form


class RenewalEventUpdateView(RenewalEventCreateView, generic.UpdateView):
    pass


class RenewalEventDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = RenewalEvent
    template_name = "subscriptions/confirm_delete.html"
    success_url = reverse_lazy("subscriptions:renewalevent-list")
