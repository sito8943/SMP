"""
Django settings for the SMP console.
"""
import os
from pathlib import Path
from urllib.parse import quote_plus

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent

SECRET_KEY = "django-insecure-smp-placeholder-secret-key"
DEBUG = True
ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,0.0.0.0,[::1]").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "subscriptions",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "wsgi.application"
ASGI_APPLICATION = "asgi.application"

DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("KOYEB_DATABASE_URL")

if not DATABASE_URL:
    db_name = os.getenv("KOYEB_DB_NAME") or os.getenv("POSTGRES_DB")
    db_user = os.getenv("KOYEB_DB_USER") or os.getenv("POSTGRES_USER")
    db_password = os.getenv("KOYEB_DB_PASSWORD") or os.getenv("POSTGRES_PASSWORD")
    db_host = os.getenv("KOYEB_DB_HOST") or os.getenv("POSTGRES_HOST")

    if db_name and db_user and db_password and db_host:
        DATABASE_URL = (
            f"postgresql://{quote_plus(db_user)}:{quote_plus(db_password)}"
            f"@{db_host}/{db_name}?sslmode=require"
        )

if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            ssl_require=True,
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": str(BASE_DIR / "db.sqlite3"),
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "subscriptions:dashboard"
LOGOUT_REDIRECT_URL = "home"

BASE_CURRENCY = "USD"
EXCHANGE_RATES = {
    "USD": 1.0,
    "EUR": 1.08,
    "GBP": 1.27,
    "MXN": 0.058,
    "ARS": 0.0011,
}
