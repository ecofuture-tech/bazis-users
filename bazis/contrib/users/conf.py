# Copyright 2026 EcoFuture Technology Services LLC and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import Literal

from django.utils.translation import gettext_lazy as _

from pydantic import Field

from bazis.core.utils.schemas import BazisSettings


class Settings(BazisSettings):
    """
    Settings class inherits from BazisSettings and defines various configuration
    parameters for the application, including the anonymous user model, OpenAPI token
    endpoint, JWT algorithm, and JWT session lifetime.

    The package must not declare or default Django settings that bind project models, such
    as AUTH_USER_MODEL (the core declares it with Django's default, a project sets
    BS_AUTH_USER_MODEL): the conf module is loaded in every project where the package is
    installed, including projects that do not use the users app. See the system check
    users.E001.
    """

    AUTH_ANONYMOUS_USER_MODEL: str = Field(
        'bazis.contrib.users.models.AnonymousUser', title=_('Default anonymous user model')
    )
    BAZIS_OPENAPI_TOKEN_URL: str = Field('/api/openapi-token/', title=_('OpenAPI token`s endpoint'))
    BAZIS_AUTH_COOKIE_NAME: str = Field('bazis_auth', title=_('Name of the user cookie'))
    #: session tokens are signed with SECRET_KEY, so only HMAC algorithms are allowed
    BAZIS_JWT_SESSION_ALG: Literal['HS256', 'HS384', 'HS512'] = Field(
        'HS256', title=_('JWT algorithm')
    )
    BAZIS_JWT_SESSION_LIFETIME: int = Field(
        86400,
        title=_('JWT lifetime'),
        json_schema_extra={'dynamic': True},
    )


settings = Settings()
