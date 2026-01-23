from django.utils.translation import gettext_lazy as _

from bazis.core.utils.apps import BaseConfig


class UsersConfig(BaseConfig):
    """
    Configuration class for the 'users' application within the Bazis project. It
    sets the application name and provides a human-readable name for the application
    using Django's translation utilities.
    """

    name = 'bazis.contrib.users'
    verbose_name = _('Users')
