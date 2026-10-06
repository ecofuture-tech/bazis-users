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

import pytest

from bazis.contrib.users.checks import check_user_model


def test_default_user_model_with_users_app(settings):
    """
    The project installs the users app (the check is registered by it), but does not set
    AUTH_USER_MODEL (the package no longer defaults it): the check names the setting to add.
    """
    settings.AUTH_USER_MODEL = 'auth.User'

    errors = check_user_model(None)

    assert [it.id for it in errors] == ['users.E001']
    assert 'BS_AUTH_USER_MODEL=users.User' in errors[0].hint


def test_valid_user_model():
    assert check_user_model(None) == []


@pytest.mark.parametrize('model', ['users.Missing', 'missing.User'])
def test_unresolvable_user_model(settings, model):
    settings.AUTH_USER_MODEL = model

    assert [it.id for it in check_user_model(None)] == ['users.E001']
