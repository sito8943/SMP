from django.contrib import admin
from django.urls import include, path

from subscriptions.views import LandingPageView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("", LandingPageView.as_view(), name="home"),
    path("", include("subscriptions.urls")),
]
