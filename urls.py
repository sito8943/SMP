from django.contrib import admin
from django.urls import include, path

from subscriptions.views import LandingPageView, SignInView, SignUpView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/login/", SignInView.as_view(), name="login"),
    path("accounts/signup/", SignUpView.as_view(), name="signup"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("", LandingPageView.as_view(), name="home"),
    path("", include("subscriptions.urls")),
]
