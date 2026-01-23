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


@pytest.mark.django_db(transaction=True)
def test_users(sample_app):
    """
    Test the user-related API endpoints, including authentication and user
    attributes for both admin and regular users.
    """
    User = get_user_model() # noqa: N806

    admin1 = User.objects.create_superuser(
        'admin1', email='admin1@site.com', password='weak_password_1'
    )
    user_1 = User.objects.create_user('user1', email='user1@site.com', password='weak_password_2')

    response = get_api_client(sample_app).get('/api/v1/users/user/')
    assert response.status_code == 401

    response = get_api_client(sample_app).get(f'/api/v1/users/user/{admin1.id}/')
    assert response.status_code == 401

    response = get_api_client(sample_app, admin1.jwt_build()).get('/api/v1/users/user/')
    assert response.status_code == 200

    response = get_api_client(sample_app, admin1.jwt_build()).get(
        f'/api/v1/users/user/{admin1.id}/'
    )
    assert response.status_code == 200

    data_admin1 = response.json()
    assert data_admin1['data']['id'] == str(admin1.id)
    assert data_admin1['data']['type'] == 'users.user'
    assert data_admin1['data']['attributes']['is_active'] is True
    assert data_admin1['data']['attributes']['is_staff'] is True
    assert data_admin1['data']['attributes']['is_superuser'] is True
    assert data_admin1['data']['attributes']['raw_password'] == '**********'
    assert 'password' not in data_admin1['data']['attributes']

    response = get_api_client(sample_app, user_1.jwt_build()).get(
        f'/api/v1/users/user/{user_1.id}/'
    )
    assert response.status_code == 200

    data_user_1 = response.json()
    assert data_user_1['data']['attributes']['is_staff'] is False
    assert data_user_1['data']['attributes']['is_superuser'] is False
