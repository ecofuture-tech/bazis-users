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

"""
Django system checks of bazis-users (see `manage.py bazis_doctor`).
"""

from django.conf import global_settings, settings
from django.contrib.auth import get_user_model
from django.core.checks import Error, register
from django.core.exceptions import ImproperlyConfigured


@register()
def check_user_model(app_configs, **kwargs):
    """
    The session tokens and the user routes need the user model of bazis-users.
    """
    from .models_abstract import UserAbstract

    # the check is registered by UsersConfig.ready(), so the users app is installed; the
    # package does not default AUTH_USER_MODEL, a project that does not set it keeps auth.User
    if settings.AUTH_USER_MODEL == global_settings.AUTH_USER_MODEL:
        return [
            Error(
                'AUTH_USER_MODEL is not set, so Django uses its default auth.User, '
                'but the project installs the users app.',
                hint=(
                    'Add BS_AUTH_USER_MODEL=users.User to the project environment (use the '
                    'label of your users app and the name of your user model if they differ).'
                ),
                id='users.E001',
            )
        ]

    try:
        user_model = get_user_model()
    except ImproperlyConfigured as err:
        return [
            Error(str(err), hint='Set BS_AUTH_USER_MODEL to an installed model.', id='users.E001')
        ]
    if not issubclass(user_model, UserAbstract):
        return [
            Error(
                f'The user model {user_model._meta.label} does not inherit UserAbstract.',
                hint=(
                    'Inherit the user model from bazis.contrib.users.models_abstract.UserAbstract '
                    'and set BS_AUTH_USER_MODEL to it.'
                ),
                id='users.E001',
            )
        ]
    return []


@register()
def check_token_route(app_configs, **kwargs):
    """
    The token endpoint is a route of the application declared by importing
    `bazis.contrib.users.token`: a project whose router imports neither it nor
    `bazis.contrib.users.router` has no login, and every route that reads the token points
    Swagger and the clients at a missing URL. Runs when the application is loaded
    (`manage.py bazis_doctor`).
    """
    from bazis.core.introspect import iter_routes_with_paths, loaded_app

    if (app := loaded_app()) is None:
        return []

    url = settings.BAZIS_OPENAPI_TOKEN_URL
    if any(
        path == url and 'POST' in (route.methods or ())
        for path, route in iter_routes_with_paths(app.routes)
    ):
        return []
    return [
        Error(
            f'The token endpoint POST {url} (BAZIS_OPENAPI_TOKEN_URL) is not registered, '
            'so nobody can log in.',
            hint=(
                'Import it in the router module of the project (BS_BAZIS_ROUTER_MODULE): '
                '`import bazis.contrib.users.token  # noqa: F401`, or register the user '
                "routes with `router.register('bazis.contrib.users.router')`."
            ),
            id='users.E002',
        )
    ]
