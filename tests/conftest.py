from django.core.management import call_command

import pytest


@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker) -> None:
    """
    Fixture to set up the Django database for the test session. This ensures that
    the 'pgtrigger' is installed before any tests are run.
    """
    with django_db_blocker.unblock():
        call_command('pgtrigger', 'install')


@pytest.fixture(scope='function')
def sample_app():
    """
    Fixture to provide an instance of the sample application for use in tests. This
    fixture has a function scope, meaning it is set up and torn down for each test
    function.
    """
    from sample.main import app

    return app
