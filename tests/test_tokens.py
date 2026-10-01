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

from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from django.utils.timezone import now

import jwt
import pytest
from bazis_test_utils.utils import get_api_client

from bazis.contrib.users import get_user_model
from bazis.contrib.users.middleware import UserRequestMiddleware
from bazis.contrib.users.models_abstract import UserMixin


def _token(payload: dict, key: str | None = None, algorithm: str = 'HS256') -> str:
    return jwt.encode(payload, key or settings.SECRET_KEY, algorithm=algorithm)


@pytest.fixture
def user(db):
    return get_user_model().objects.create_user('token_user', password='weak_password_3')


def _get_me(app, token: str):
    return get_api_client(app, token).get('/api/v1/users/user/')


@pytest.mark.django_db(transaction=True)
def test_valid_token(sample_app, user):
    token = user.jwt_build(auth_type='password')
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
    assert payload['sub'] == user.username
    assert payload['auth_type'] == 'password'
    assert payload['iat'] < payload['exp']
    assert _get_me(sample_app, token).status_code == 200


@pytest.mark.django_db(transaction=True)
def test_token_issued_in_the_future(sample_app, user):
    # a token issued by a server whose clock is ahead
    token = _token(
        {'sub': user.username, 'iat': now() + timedelta(seconds=5), 'exp': now() + timedelta(hours=1)}
    )
    assert _get_me(sample_app, token).status_code == 200


@pytest.mark.django_db(transaction=True)
def test_expired_token(sample_app, user):
    token = _token({'sub': user.username, 'exp': now() - timedelta(seconds=1)})
    response = _get_me(sample_app, token)
    assert response.status_code == 401
    assert response.json()['errors'][0]['detail'] == 'Token has expired'


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    'make_token',
    [
        # signed with another key
        lambda u: _token({'sub': u.username, 'exp': now() + timedelta(hours=1)}, key='x' * 40),
        # no subject
        lambda u: _token({'exp': now() + timedelta(hours=1)}),
        # unsigned
        lambda u: jwt.encode(
            {'sub': u.username, 'exp': now() + timedelta(hours=1)}, None, algorithm='none'
        ),
        # algorithm other than the configured one
        lambda u: _token({'sub': u.username, 'exp': now() + timedelta(hours=1)}, algorithm='HS512'),
        # not a token at all
        lambda u: 'garbage',
    ],
    ids=['foreign-key', 'no-sub', 'alg-none', 'other-alg', 'garbage'],
)
def test_invalid_token(sample_app, user, make_token):
    response = _get_me(sample_app, make_token(user))
    assert response.status_code == 401
    assert response.json()['errors'][0]['detail'] == 'Token is invalid'


@pytest.mark.django_db(transaction=True)
def test_inactive_user_token(sample_app, user):
    token = user.jwt_build()
    user.is_active = False
    user.save()
    assert _get_me(sample_app, token).status_code == 401


@pytest.mark.django_db
def test_middleware_resets_user_context(user):
    seen = []

    def view(request):
        seen.append(UserMixin.CTX_USER_REQUEST.get())
        return 'response'

    middleware = UserRequestMiddleware(view)
    request = RequestFactory().get('/')

    request.user = user
    assert middleware(request) == 'response'
    # the user does not stay in the context after the request
    assert UserMixin.CTX_USER_REQUEST.get() is None

    request.user = AnonymousUser()
    middleware(request)
    assert seen == [user, None]


@pytest.mark.django_db(transaction=True)
def test_token_without_expiration_is_anonymous(sample_app, user):
    """
    A token without expiration identifies nobody (it is not a session token, e.g. the
    authorization store token of bazis-authing in the same cookie).
    """
    from bazis.contrib.users.service import get_token_data

    token = _token({'sub': user.username})
    assert get_token_data(token_header=None, token_param=None, token_cookie=token) == {}
    assert _get_me(sample_app, token).status_code == 401


@pytest.mark.django_db(transaction=True)
def test_user_cannot_grant_himself_groups(sample_app, user):
    """
    groups and user_permissions are excluded from the user schema: the relationships
    endpoints must not change them (privilege escalation through Django permissions).
    """
    from django.contrib.auth.models import Group, Permission

    admins = Group.objects.create(name='admins')
    admins.permissions.set(Permission.objects.all())
    client = get_api_client(sample_app, user.jwt_build())

    response = client.post(
        f'/api/v1/users/user/{user.id}/relationships/groups',
        json_data={'data': [{'id': str(admins.id), 'type': 'auth.group'}]},
    )
    assert response.status_code == 403
    assert not user.groups.exists()

    permission = Permission.objects.first()
    response = client.post(
        f'/api/v1/users/user/{user.id}/relationships/user_permissions',
        json_data={'data': [{'id': str(permission.id), 'type': 'auth.permission'}]},
    )
    assert response.status_code == 403
    assert not user.user_permissions.exists()
