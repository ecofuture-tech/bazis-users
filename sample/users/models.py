from bazis.contrib.users.models_abstract import AnonymousUserAbstract, UserAbstract
from bazis.core.models_abstract import JsonApiMixin, UuidMixin


class User(JsonApiMixin, UuidMixin, UserAbstract):
    """
    Represents a user in the system, combining JSON API support, UUID functionality,
    and user-specific attributes and methods.
    """

    pass


class AnonymousUser(AnonymousUserAbstract):
    """
    Represents an anonymous user with attributes and methods specific to users who
    are not logged in.
    """

    pass
