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

from bazis.contrib.users.checks import check_user_model
from bazis.core.introspect import packages, validate_manifest


def test_manifest_is_valid():
    assert validate_manifest('bazis.contrib.users') == []


def test_manifest_is_found():
    users = {it['name']: it for it in packages()}['bazis-users']
    assert users['module'] == 'bazis.contrib.users'
    assert users['manifest']['package']['name'] == 'bazis-users'


def test_user_model_check(monkeypatch):
    assert check_user_model(None) == []

    from django.contrib.auth.models import Group

    monkeypatch.setattr('bazis.contrib.users.checks.get_user_model', lambda: Group)
    assert [it.id for it in check_user_model(None)] == ['users.E001']
