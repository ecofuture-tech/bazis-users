from django.utils.translation import gettext_lazy as _

from pydantic import Field

from jose.constants import Algorithms

from bazis.core.utils.schemas import BazisSettings


class Settings(BazisSettings):
    """
    Settings class inherits from BazisSettings and defines various configuration
    parameters for the application, including user models, OpenAPI token endpoint,
    JWT algorithm, and JWT session lifetime.
    """

    AUTH_USER_MODEL: str = Field('users.User', title=_('Default user model'))
    AUTH_ANONYMOUS_USER_MODEL: str = Field(
        'bazis.contrib.users.models.AnonymousUser', title=_('Default anonymous user model')
    )
    BAZIS_OPENAPI_TOKEN_URL: str = Field('/api/openapi-token/', title=_('OpenAPI token`s endpoint'))
    BAZIS_AUTH_COOKIE_NAME: str = Field('bazis_auth', title=_('Name of the user cookie'))
    BAZIS_JWT_SESSION_ALG: str = Field(Algorithms.HS256, title=_('JWT algorithm'))
    BAZIS_JWT_SESSION_LIFETIME: int = Field(86400, title=_('JWT lifetime'), dynamic=True)


settings = Settings()
