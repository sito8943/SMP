"""
URL configuration for sirp_django_project.

This file intentionally keeps the default Django routing setup.
"""

from django.contrib import admin
from django.urls import path

urlpatterns = [
    path("admin/", admin.site.urls),
]
