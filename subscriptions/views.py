from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
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
from .services import summarize_costs, upcoming_renewals


def scope_queryset_for_user(queryset, user, owner_lookup: str = "owner"):
    if user.is_superuser:
        return queryset
    return queryset.filter(**{owner_lookup: user})


class SignUpView(generic.CreateView):
    form_class = UserCreationForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy("subscriptions:dashboard")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("subscriptions:dashboard")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response


class LandingPageView(generic.TemplateView):
    template_name = "home.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("subscriptions:dashboard")
        return super().dispatch(request, *args, **kwargs)


class UserScopedQuerysetMixin:
    owner_lookup = "owner"

    def scope_queryset(self, queryset):
        return scope_queryset_for_user(queryset, self.request.user, self.owner_lookup)

    def get_queryset(self):
        return self.scope_queryset(super().get_queryset())


class OwnerAssignCreateMixin:
    def form_valid(self, form):
        if not form.instance.owner_id:
            form.instance.owner = self.request.user
        return super().form_valid(form)


class DashboardView(LoginRequiredMixin, generic.TemplateView):
    template_name = "subscriptions/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        subs = scope_queryset_for_user(
            Subscription.objects.select_related("provider", "billing_cycle"), self.request.user
        )
        active_subs = subs.filter(status=SubscriptionStatus.ACTIVE)
        notification_rules = scope_queryset_for_user(
            NotificationRule.objects.all(),
            self.request.user,
            owner_lookup="subscription__owner",
        )
        pending_renewals = scope_queryset_for_user(
            RenewalEvent.objects.filter(is_processed=False),
            self.request.user,
            owner_lookup="subscription__owner",
        )
        summary = summarize_costs(active_subs)

        context["providers"] = scope_queryset_for_user(
            Provider.objects.all(), self.request.user
        ).count()
        context["subscriptions"] = subs.count()
        context["billing_cycles"] = scope_queryset_for_user(
            BillingCycle.objects.all(), self.request.user
        ).count()
        context["notifications"] = notification_rules.count()
        context["renewals_pending"] = pending_renewals.count()
        context["monthly_total"] = summary.monthly_total
        context["annual_total"] = summary.annual_total
        context["upcoming_renewals"] = upcoming_renewals(user=self.request.user)
        context["base_currency"] = settings.BASE_CURRENCY
        return context


class ProviderListView(UserScopedQuerysetMixin, LoginRequiredMixin, generic.ListView):
    model = Provider
    template_name = "subscriptions/provider_list.html"


class ProviderDetailView(UserScopedQuerysetMixin, LoginRequiredMixin, generic.DetailView):
    model = Provider
    template_name = "subscriptions/provider_detail.html"


class ProviderCreateView(OwnerAssignCreateMixin, LoginRequiredMixin, generic.CreateView):
    model = Provider
    fields = ["name", "category", "website"]
    template_name = "subscriptions/form.html"
    success_url = reverse_lazy("subscriptions:provider-list")


class ProviderUpdateView(
    UserScopedQuerysetMixin, ProviderCreateView, generic.UpdateView
):
    pass


class ProviderDeleteView(UserScopedQuerysetMixin, LoginRequiredMixin, generic.DeleteView):
    model = Provider
    template_name = "subscriptions/confirm_delete.html"
    success_url = reverse_lazy("subscriptions:provider-list")


class BillingCycleListView(UserScopedQuerysetMixin, LoginRequiredMixin, generic.ListView):
    model = BillingCycle
    template_name = "subscriptions/billingcycle_list.html"


class BillingCycleCreateView(OwnerAssignCreateMixin, LoginRequiredMixin, generic.CreateView):
    model = BillingCycle
    fields = ["interval", "unit"]
    template_name = "subscriptions/form.html"
    success_url = reverse_lazy("subscriptions:billingcycle-list")


class BillingCycleUpdateView(
    UserScopedQuerysetMixin, BillingCycleCreateView, generic.UpdateView
):
    pass


class BillingCycleDeleteView(
    UserScopedQuerysetMixin, LoginRequiredMixin, generic.DeleteView
):
    model = BillingCycle
    template_name = "subscriptions/confirm_delete.html"
    success_url = reverse_lazy("subscriptions:billingcycle-list")


class SubscriptionListView(UserScopedQuerysetMixin, LoginRequiredMixin, generic.ListView):
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
        context["providers"] = scope_queryset_for_user(Provider.objects.all(), self.request.user)
        context["selected_provider"] = self.request.GET.get("provider", "")
        context["selected_status"] = self.request.GET.get("status", "")
        context["cost_min"] = self.request.GET.get("cost_min", "")
        context["cost_max"] = self.request.GET.get("cost_max", "")
        context["order"] = self.request.GET.get("order", "")
        return context


class SubscriptionDetailView(UserScopedQuerysetMixin, LoginRequiredMixin, generic.DetailView):
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


class SubscriptionFormMixin:
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
        if "provider" in form.fields:
            form.fields["provider"].queryset = scope_queryset_for_user(
                Provider.objects.all(), self.request.user
            )
        if "billing_cycle" in form.fields:
            form.fields["billing_cycle"].queryset = scope_queryset_for_user(
                BillingCycle.objects.all(), self.request.user
            )
        for field_name in ("start_date", "next_billing_date", "cancellation_date"):
            if field_name in form.fields:
                form.fields[field_name].widget.input_type = "date"
        return form


class SubscriptionCreateView(
    OwnerAssignCreateMixin, LoginRequiredMixin, SubscriptionFormMixin, generic.CreateView
):
    def form_valid(self, form):
        response = super().form_valid(form)
        SubscriptionHistory.objects.create(
            subscription=self.object,
            event_type=SubscriptionHistory.EventType.CREATED,
            description="Subscription created",
        )
        return response


class SubscriptionUpdateView(
    UserScopedQuerysetMixin,
    OwnerAssignCreateMixin,
    LoginRequiredMixin,
    SubscriptionFormMixin,
    generic.UpdateView,
):
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


class SubscriptionDeleteView(UserScopedQuerysetMixin, LoginRequiredMixin, generic.DeleteView):
    model = Subscription
    template_name = "subscriptions/confirm_delete.html"
    success_url = reverse_lazy("subscriptions:subscription-list")


class SubscriptionStatusActionView(LoginRequiredMixin, View):
    action_name = ""

    def post(self, request, pk):
        queryset = scope_queryset_for_user(Subscription.objects.all(), request.user)
        subscription = get_object_or_404(queryset, pk=pk)
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


class NotificationRuleListView(
    UserScopedQuerysetMixin, LoginRequiredMixin, generic.ListView
):
    model = NotificationRule
    template_name = "subscriptions/notificationrule_list.html"
    owner_lookup = "subscription__owner"

    def get_queryset(self):
        return super().get_queryset().select_related("subscription")


class NotificationRuleCreateView(LoginRequiredMixin, generic.CreateView):
    model = NotificationRule
    fields = ["subscription", "timing", "is_enabled"]
    template_name = "subscriptions/form.html"
    success_url = reverse_lazy("subscriptions:notificationrule-list")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if "subscription" in form.fields:
            form.fields["subscription"].queryset = scope_queryset_for_user(
                Subscription.objects.all(), self.request.user
            )
        return form


class NotificationRuleUpdateView(
    UserScopedQuerysetMixin, NotificationRuleCreateView, generic.UpdateView
):
    owner_lookup = "subscription__owner"


class NotificationRuleDeleteView(
    UserScopedQuerysetMixin, LoginRequiredMixin, generic.DeleteView
):
    model = NotificationRule
    template_name = "subscriptions/confirm_delete.html"
    success_url = reverse_lazy("subscriptions:notificationrule-list")
    owner_lookup = "subscription__owner"


class RenewalEventListView(UserScopedQuerysetMixin, LoginRequiredMixin, generic.ListView):
    model = RenewalEvent
    template_name = "subscriptions/renewalevent_list.html"
    owner_lookup = "subscription__owner"

    def get_queryset(self):
        return super().get_queryset().select_related("subscription")


class RenewalEventCreateView(LoginRequiredMixin, generic.CreateView):
    model = RenewalEvent
    fields = ["subscription", "renewal_date", "amount_amount", "amount_currency", "is_processed"]
    template_name = "subscriptions/form.html"
    success_url = reverse_lazy("subscriptions:renewalevent-list")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if "subscription" in form.fields:
            form.fields["subscription"].queryset = scope_queryset_for_user(
                Subscription.objects.all(), self.request.user
            )
        if "renewal_date" in form.fields:
            form.fields["renewal_date"].widget.input_type = "date"
        return form


class RenewalEventUpdateView(
    UserScopedQuerysetMixin, RenewalEventCreateView, generic.UpdateView
):
    owner_lookup = "subscription__owner"


class RenewalEventDeleteView(UserScopedQuerysetMixin, LoginRequiredMixin, generic.DeleteView):
    model = RenewalEvent
    template_name = "subscriptions/confirm_delete.html"
    success_url = reverse_lazy("subscriptions:renewalevent-list")
    owner_lookup = "subscription__owner"
