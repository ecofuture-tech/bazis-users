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
The language of a user (`language`): one of the languages of the project (LANGUAGES), or
blank when the user has not chosen one. The user reads and changes it himself; a client
(bazis-front) adopts it at a login and saves the language of its interface there.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest
from bazis_test_utils.utils import get_api_client

from bazis.contrib.users import get_user_model


User = get_user_model()
SAMPLE = Path(__file__).resolve().parent.parent / 'sample'


def _patch(user, **attributes) -> dict:
    return {'data': {'id': str(user.id), 'type': 'users.user', 'attributes': attributes}}


@pytest.mark.django_db(transaction=True)
def test_user_reads_and_changes_his_language(sample_app):
    user = User.objects.create_user('user', password='weak_password_1')
    client = get_api_client(sample_app, user.jwt_build())
    url = f'/api/v1/users/user/{user.id}/'

    assert client.get(url).json()['data']['attributes']['language'] == ''

    assert client.patch(url, json_data=_patch(user, language='ru')).status_code == 200
    user.refresh_from_db()
    assert user.language == 'ru'
    assert client.get(url).json()['data']['attributes']['language'] == 'ru'

    # blank: no language chosen
    assert client.patch(url, json_data=_patch(user, language='')).status_code == 200
    user.refresh_from_db()
    assert user.language == ''


@pytest.mark.django_db(transaction=True)
def test_the_schema_lists_the_languages_of_the_project(sample_app):
    user = User.objects.create_user('user', password='weak_password_1')
    client = get_api_client(sample_app, user.jwt_build())

    schema = client.get(f'/api/v1/users/user/{user.id}/schema_update/').json()

    [attributes] = [it for name, it in schema['$defs'].items() if name.endswith('__Attributes')]
    language = attributes['properties']['language']
    assert language['enum'] == ['en', 'ru']
    assert language['enumDict'] == {'en': 'English', 'ru': 'Русский'}


def test_the_migrations_do_not_depend_on_the_languages_of_the_project():
    """
    The choices of the field are the languages of the project: a callable, so that a
    change of LANGUAGES does not need a migration (of the project, or of the package).
    """
    env = {
        **os.environ,
        'BS_DATABASES__DEFAULT__NAME': 'users_no_such_database',
        'BS_LANGUAGES': '[["en", "English"], ["de", "Deutsch"]]',
    }
    done = subprocess.run(
        [sys.executable, 'manage.py', 'makemigrations', 'users', '--check', '--dry-run'],
        cwd=SAMPLE, env=env, capture_output=True, text=True, timeout=300,
    )

    assert done.returncode == 0, done.stdout[-3000:] + done.stderr[-3000:]
