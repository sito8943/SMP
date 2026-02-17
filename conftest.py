import os

import django
import pytest
from django.test.utils import (
    setup_databases,
    setup_test_environment,
    teardown_databases,
    teardown_test_environment,
)


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
django.setup()


@pytest.fixture(scope="session", autouse=True)
def django_test_setup(request):
    setup_test_environment()
    db_cfg = setup_databases(verbosity=1, interactive=False)
    request.addfinalizer(lambda: teardown_databases(db_cfg, verbosity=1))
    request.addfinalizer(teardown_test_environment)
