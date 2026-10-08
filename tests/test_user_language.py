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
The language of a user (`UserLanguageMixin.language`, opt-in): a code of the languages of
the project (LANGUAGES), or None when the user has not chosen one. The user reads and changes
it himself; a client (bazis-front) adopts it at a login and saves the language of its
interface there.
"""

import os
import subprocess
import sys
from pathlib import Path

from django.conf import settings

from fastapi.testclient import TestClient

import pytest
from bazis_test_utils.utils import get_api_client

from bazis.contrib.users import get_user_model
from bazis.contrib.users.models_abstract import UserAbstract
from bazis.core.errors import JsonApiBazisException


User = get_user_model()
SAMPLE = Path(__file__).resolve().parent.parent / 'sample'


def _patch(user, **attributes) -> dict:
    return {'data': {'id': str(user.id), 'type': 'users.user', 'attributes': attributes}}


@pytest.fixture
def user():
    return User.objects.create_user('user', password='weak_password_1')


@pytest.mark.django_db(transaction=True)
def test_user_reads_and_changes_his_language(sample_app, user):
    client = get_api_client(sample_app, user.jwt_build())
    url = f'/api/v1/users/user/{user.id}/'

    assert client.get(url).json()['data']['attributes']['language'] is None

    assert client.patch(url, json_data=_patch(user, language='ru')).status_code == 200
    user.refresh_from_db()
    assert user.language == 'ru'
    assert client.get(url).json()['data']['attributes']['language'] == 'ru'

    # the code of LANGUAGES of a regional or differently written code
    assert client.patch(url, json_data=_patch(user, language='RU_ru')).status_code == 200
    user.refresh_from_db()
    assert user.language == 'ru'

    # None (or blank): no language chosen
    for value in (None, ''):
        user.language = 'en'
        user.save()
        assert client.patch(url, json_data=_patch(user, language=value)).status_code == 200
        user.refresh_from_db()
        assert user.language is None


@pytest.mark.django_db(transaction=True)
def test_a_language_the_project_does_not_have(sample_app, user):
    client = get_api_client(sample_app, user.jwt_build())

    response = client.patch(f'/api/v1/users/user/{user.id}/', json_data=_patch(user, language='de'))

    assert response.status_code == 422, response.text
    [error] = response.json()['errors']
    assert error['source'] == {'pointer': '/data/attributes/language'}
    assert 'en, ru' in error['detail']
    user.refresh_from_db()
    assert user.language is None


@pytest.mark.django_db(transaction=True)
def test_a_stale_language_does_not_block_the_user(sample_app, user):
    """
    A language the project no longer has (removed from LANGUAGES) stays until the language
    is written: the user logs in, and every save that does not change the language passes.
    """
    User.objects.filter(pk=user.pk).update(language='de')

    response = TestClient(sample_app).post(
        settings.BAZIS_OPENAPI_TOKEN_URL, data={'username': 'user', 'password': 'weak_password_1'}
    )
    assert response.status_code == 200, response.text

    user = User.objects.get(pk=user.pk)
    user.save(update_fields=['last_login'])
    user.first_name = 'Me'
    user.set_password('weak_password_2')
    user.save()
    deferred = User.objects.defer('language').get(pk=user.pk)
    deferred.last_name = 'Myself'
    deferred.save()
    # a change of another field through the routes
    client = get_api_client(sample_app, user.jwt_build())
    response = client.patch(f'/api/v1/users/user/{user.id}/', json_data=_patch(user, first_name='I'))
    assert response.status_code == 200, response.text
    # reloaded after another change of the language in the database
    user.language = 'ru'
    user.save()
    User.objects.filter(pk=user.pk).update(language='de')
    user.refresh_from_db()
    user.save()

    assert User.objects.get(pk=user.pk).language == 'de'

    # writing it validates it
    user.language = 'fr'
    with pytest.raises(JsonApiBazisException):
        user.save(update_fields=['language'])
    deferred.language = 'fr'
    with pytest.raises(JsonApiBazisException):
        deferred.save()


@pytest.mark.django_db(transaction=True)
def test_a_new_user_with_a_language_the_project_does_not_have():
    with pytest.raises(JsonApiBazisException):
        User.objects.create_user('user', password='weak_password_1', language='de')
    assert not User.objects.filter(username='user').exists()

    assert User.objects.create_user('other', language='RU').language == 'ru'


@pytest.mark.django_db(transaction=True)
def test_the_language_of_another_user(sample_app, user):
    other = User.objects.create_user('other', password='weak_password_2', language='en')
    client = get_api_client(sample_app, user.jwt_build())

    response = client.patch(f'/api/v1/users/user/{other.id}/', json_data=_patch(other, language='ru'))

    assert response.status_code == 404
    other.refresh_from_db()
    assert other.language == 'en'


@pytest.mark.django_db(transaction=True)
def test_the_schema_lists_the_languages_of_the_project(sample_app, user):
    client = get_api_client(sample_app, user.jwt_build())

    schema = client.get(f'/api/v1/users/user/{user.id}/schema_update/').json()

    [attributes] = [it for name, it in schema['$defs'].items() if name.endswith('__Attributes')]
    language = attributes['properties']['language']
    assert language['enum'] == ['en', 'ru']
    assert language['enumDict'] == {'en': 'English', 'ru': 'Русский'}
    assert language['nullable'] is True


def test_the_language_is_opt_in():
    """
    A user model on UserAbstract alone has no language: adding the field needs a migration
    of the user model of the project.
    """
    assert 'language' not in {field.name for field in UserAbstract._meta.get_fields()}


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
