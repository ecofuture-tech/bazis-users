try:
    from importlib.metadata import PackageNotFoundError, version
    __version__ = version('bazis-users')
except PackageNotFoundError:
    __version__ = 'dev'

from django.conf import settings
from django.contrib.auth import get_user_model

from bazis.core.utils.imp import import_class


def get_anonymous_user_model():
    """
    Retrieve the anonymous user model class specified in the Django settings.
    """
    return import_class(settings.AUTH_ANONYMOUS_USER_MODEL)
