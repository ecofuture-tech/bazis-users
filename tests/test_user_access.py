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
from bazis_test_utils.utils import get_api_client

from bazis.contrib.users import get_user_model


User = get_user_model()


def _patch(user, **attributes) -> dict:
    return {
        'data': {
            'id': str(user.id),
            'type': 'users.user',
            'bs:action': 'change',
            'attributes': attributes,
        }
    }


@pytest.fixture
def people():
    superuser = User.objects.create_superuser('root', password='weak_password_1')
    staff = User.objects.create_user('staff', password='weak_password_2', is_staff=True)
    user = User.objects.create_user('user', password='weak_password_3')
    other = User.objects.create_user('other', password='weak_password_4')
    return superuser, staff, user, other


@pytest.mark.django_db(transaction=True)
def test_user_sees_and_changes_only_himself(sample_app, people):
    """
    Any authenticated user could list, change (including the password) and delete any
    user through the user routes.
    """
    _, _, user, other = people
    client = get_api_client(sample_app, user.jwt_build())

    response = client.get('/api/v1/users/user/')
    assert [it['id'] for it in response.json()['data']] == [str(user.id)]
    assert client.get(f'/api/v1/users/user/{other.id}/').status_code == 404

    response = client.patch(
        f'/api/v1/users/user/{other.id}/', json_data=_patch(other, raw_password='hijacked1')
    )
    assert response.status_code == 404
    other.refresh_from_db()
    assert other.check_password('weak_password_4')

    response = client.patch(f'/api/v1/users/user/{user.id}/', json_data=_patch(user, first_name='Me'))
    assert response.status_code == 200

    assert client.delete(f'/api/v1/users/user/{user.id}/').status_code == 403
    assert User.objects.filter(id=user.id).exists()


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize('field', ['is_staff', 'is_superuser', 'is_active'])
def test_only_superuser_changes_privileges(sample_app, people, field):
    superuser, staff, user, _ = people
    value = field != 'is_active'

    for actor in (user, staff):
        response = get_api_client(sample_app, actor.jwt_build()).patch(
            f'/api/v1/users/user/{user.id}/', json_data=_patch(user, **{field: value})
        )
        assert response.status_code == 403
        user.refresh_from_db()
        assert getattr(user, field) is not value

    response = get_api_client(sample_app, superuser.jwt_build()).patch(
        f'/api/v1/users/user/{user.id}/', json_data=_patch(user, **{field: value})
    )
    assert response.status_code == 200
    user.refresh_from_db()
    assert getattr(user, field) is value


@pytest.mark.django_db(transaction=True)
def test_only_staff_creates_users(sample_app, people):
    _, staff, user, _ = people
    payload = {
        'data': {
            'type': 'users.user',
            'bs:action': 'add',
            'attributes': {'username': 'new', 'raw_password': 'weak_password_5'},
        }
    }
    response = get_api_client(sample_app, user.jwt_build()).post('/api/v1/users/user/', json_data=payload)
    assert response.status_code == 403

    payload['data']['attributes']['is_superuser'] = True
    response = get_api_client(sample_app, staff.jwt_build()).post('/api/v1/users/user/', json_data=payload)
    assert response.status_code == 403
    assert not User.objects.filter(username='new').exists()

    del payload['data']['attributes']['is_superuser']
    response = get_api_client(sample_app, staff.jwt_build()).post('/api/v1/users/user/', json_data=payload)
    assert response.status_code == 201
