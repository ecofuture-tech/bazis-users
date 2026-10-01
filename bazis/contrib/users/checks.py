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

from django.contrib.auth import get_user_model
from django.core.checks import Error, register
from django.core.exceptions import ImproperlyConfigured


@register()
def check_user_model(app_configs, **kwargs):
    """
    The session tokens and the user routes need the user model of bazis-users.
    """
    from .models_abstract import UserAbstract

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
