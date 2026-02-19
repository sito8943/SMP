# Subscription Intelligence Research Platform (SIRP)

[![Deploy to Koyeb](https://www.koyeb.com/static/images/deploy/button.svg)](https://app.koyeb.com/deploy?name=ci-cd-primer&type=git&repository=sito8943%2Fsirp&branch=main&instance_type=free&regions=fra&instances_min=0&autoscaling_sleep_idle_delay=3900&env%5BDJANGO_ALLOWED_HOSTS%5D=%7B%7B+KOYEB_PUBLIC_DOMAIN+%7D%7D&ports=5000%3Bhttp%3B%2F&hc_protocol%5B5000%5D=tcp&hc_grace_period%5B5000%5D=5&hc_interval%5B5000%5D=30&hc_restart_limit%5B5000%5D=3&hc_timeout%5B5000%5D=5&hc_path%5B5000%5D=%2F&hc_method%5B5000%5D=get)

[Demo HERE!!!](https://satisfied-josefina-subscription-school-7d68d80a.koyeb.app/accounts/login/)

<img width="2940" height="1912" alt="image" src="https://github.com/user-attachments/assets/d6efec08-9017-43b7-9dd5-156e9be9388d" />

SIRP is a Django web application to manage recurring subscriptions with user-scoped data, dashboards, lifecycle actions, and renewal tracking.

## Features

- Authentication: sign up, sign in, sign out.
- User-scoped CRUD for:
  - Providers
  - Billing cycles
  - Subscriptions
  - Notification rules
  - Renewal events
- Subscription lifecycle actions:
  - Pause
  - Resume
  - Cancel
- Subscription history timeline (created/updated/status changes).
- Dashboard with:
  - Entity counts
  - Monthly and annual totals (base currency)
  - Upcoming renewals
- Subscription list filters (provider, status, cost range, ordering).

## Tech Stack

- Python + Django 5
- Templates + UIkit
- Gunicorn + WhiteNoise
- PostgreSQL (primary) via `DATABASE_URL`
- SQLite fallback for local/dev convenience
- Quality tooling: Ruff + mypy + pre-commit
- CI: GitHub Actions

## Project Structure

```text
.
├── asgi.py
├── manage.py
├── settings.py
├── urls.py
├── wsgi.py
├── Procfile
├── pyproject.toml
├── requirements.in
├── requirements.txt
├── templates/
├── subscriptions/
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   ├── services.py
│   ├── urls.py
│   └── tests/
│       ├── test_views.py
│       ├── test_services.py
│       └── test_models.py
└── .github/
    ├── dependabot.yml
    └── workflows/ci.yml
```

## Local Setup

1. Create and activate a virtual environment.
2. Install dependencies.
3. Run migrations.
4. Start the server.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Dependency Management

Install `pip-tools` once in your active virtualenv:

```bash
pip install pip-tools
```

- `requirements.in` contains direct dependencies.
- `requirements.txt` is the lock file consumed by local setup and CI.

Regenerate lock file without upgrading versions:

```bash
pip-compile --output-file=requirements.txt requirements.in
```

Upgrade all dependencies and refresh lock file:

```bash
pip-compile --upgrade --output-file=requirements.txt requirements.in
```

Upgrade a single dependency and refresh lock file:

```bash
pip-compile --upgrade-package Django --output-file=requirements.txt requirements.in
```

## Environment Variables

Database configuration priority in `settings.py`:

1. `DATABASE_URL`
2. `KOYEB_DATABASE_URL`
3. Built URL from split variables:
   - `KOYEB_DB_NAME`, `KOYEB_DB_USER`, `KOYEB_DB_PASSWORD`, `KOYEB_DB_HOST`
   - or `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`
4. SQLite fallback (`db.sqlite3`)

Useful variables:

- `DATABASE_URL`
- `KOYEB_DATABASE_URL`
- `KOYEB_DB_NAME`
- `KOYEB_DB_USER`
- `KOYEB_DB_PASSWORD`
- `KOYEB_DB_HOST`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_HOST`
- `DJANGO_ALLOWED_HOSTS`

Example:

```bash
export DATABASE_URL='postgresql://user:password@host/dbname?sslmode=require'
```

## Quality and Checks

### Ruff

```bash
ruff check .
```

### mypy

```bash
mypy --config-file pyproject.toml
```

### Django migration drift check

```bash
python manage.py makemigrations --check --dry-run
```

### Run tests

```bash
python manage.py test
```

## Pre-commit

Install git hooks:

```bash
pre-commit install
```

Run all hooks manually:

```bash
pre-commit run --all-files
```

Configured hooks include:

- Basic file hygiene hooks
- Ruff
- mypy
- Django migration check (`makemigrations --check --dry-run`)

## CI (GitHub Actions)

`/.github/workflows/ci.yml` runs:

1. Dependency install
2. Ruff lint
3. mypy type check
4. Migration drift check
5. Migrations
6. Django startup smoke checks
7. Test suite

## Deployment

`Procfile` runs:

1. `python manage.py migrate --noinput`
2. `python manage.py collectstatic --noinput`
3. `gunicorn wsgi:application ...`

For production, define environment variables in your platform (for example Koyeb) instead of relying on local `.env`.
