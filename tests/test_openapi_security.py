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
What the OpenAPI schema tells a client generator about the token: the security scheme,
which operations need the token, and the 401 error.
"""

from django.conf import settings

import pytest
from bazis_test_utils.utils import get_api_client

from bazis.contrib.users import get_user_model
from bazis.contrib.users.routes_abstract import UserOpenApiMixin
from bazis.core.errors import SchemaErrors
from bazis.core.routes_abstract.initial import InitialRouteBase, http_get


SCHEMA_ERRORS = '#/components/schemas/SchemaErrors'
TOKEN = {'OAuth2PasswordBearer': []}

ENTITY = '/api/v1/entity'


@pytest.fixture(scope='module')
def spec():
    from bazis.core.app import app

    return app.openapi()


@pytest.fixture(scope='module')
def operations(spec):
    return {
        (path, method.upper()): operation
        for path, item in spec['paths'].items()
        for method, operation in item.items()
    }


def route_operations(operations, prefix):
    found = {key: op for key, op in operations.items() if key[0].startswith(prefix)}
    assert found
    return found


def test_security_scheme(spec):
    flows = spec['components']['securitySchemes']['OAuth2PasswordBearer']['flows']
    assert flows['password']['tokenUrl'] == settings.BAZIS_OPENAPI_TOKEN_URL


@pytest.mark.parametrize(
    'prefix',
    [f'{ENTITY}/extended_entity', '/api/v1/users/user'],
)
def test_token_required(operations, prefix):
    """UserRequiredRouteBase and the user routes: no token, no access."""
    for key, operation in route_operations(operations, prefix).items():
        assert operation['security'] == [TOKEN], key


@pytest.mark.parametrize(
    'prefix',
    [f'{ENTITY}/parent_entity', f'{ENTITY}/child_entity', f'{ENTITY}/dependent_entity'],
)
def test_token_optional(operations, prefix):
    """UserRouteBase: a request without a token is anonymous, the empty requirement says so."""
    for key, operation in route_operations(operations, prefix).items():
        assert operation['security'] == [TOKEN, {}], key


@pytest.mark.parametrize(
    'prefix',
    [
        f'{ENTITY}/extended_entity',
        '/api/v1/users/user',
        f'{ENTITY}/parent_entity',
        f'{ENTITY}/child_entity',
    ],
)
def test_route_operations_document_unauthorized(operations, prefix):
    for key, operation in route_operations(operations, prefix).items():
        refs = {c['schema']['$ref'] for c in operation['responses']['401']['content'].values()}
        assert refs == {SCHEMA_ERRORS}, key


def test_other_operations(operations):
    """The token endpoint answers 401 to wrong credentials; the others do not use the token."""
    token = operations[(settings.BAZIS_OPENAPI_TOKEN_URL, 'POST')]
    assert 'security' not in token
    assert '401' in token['responses']

    health = operations[('/api/healthcheck', 'GET')]
    assert 'security' not in health
    assert '401' not in health['responses']


@pytest.mark.django_db(transaction=True)
def test_documented_unauthorized_is_what_the_routes_return(sample_app):
    """The required route fails without a token, the optional one only with a wrong token."""
    required = get_api_client(sample_app).get(f'{ENTITY}/extended_entity/')
    assert required.status_code == 401
    assert SchemaErrors.model_validate(required.json()).errors[0].status == 401

    assert get_api_client(sample_app).get(f'{ENTITY}/parent_entity/').status_code == 200

    wrong = get_api_client(sample_app, 'not-a-token').get(f'{ENTITY}/parent_entity/')
    assert wrong.status_code == 401
    assert SchemaErrors.model_validate(wrong.json()).errors[0].status == 401


def refs_of(operation, status):
    response = operation['responses'].get(status)
    return None if response is None else {
        c['schema']['$ref'] for c in response['content'].values()
    }


def test_no_dict_data_route(operations):
    """
    UserRouteBase has no `/{item_id}/dict_data/` (all the attributes of an item, past the
    schema of the route) and no 403 of its own.
    """
    assert not [path for path, _ in operations if path.endswith('/dict_data/')]
    for prefix in (f'{ENTITY}/parent_entity', f'{ENTITY}/extended_entity'):
        for (path, method), operation in route_operations(operations, prefix).items():
            if operation['x-bazis']['kind'] == 'relationship':
                continue  # the 403 of the core, see its tests
            assert refs_of(operation, '403') is None, (method, path)


def test_forbidden_of_user_routes(operations):
    """Only staff creates and deletes users, only a superuser changes their privileges."""
    for (path, method), operation in route_operations(operations, '/api/v1/users/user').items():
        kind = operation['x-bazis']['kind']
        expected = {'create', 'update', 'delete', 'relationship'}
        assert (refs_of(operation, '403') == {SCHEMA_ERRORS}) == (kind in expected), (method, path)


@pytest.mark.django_db(transaction=True)
def test_documented_forbidden_is_what_the_routes_return(sample_app):
    user = get_user_model().objects.create_user('plain_user', password='weak_password_4')
    client = get_api_client(sample_app, user.jwt_build(auth_type='password'))

    delete = client.client.delete(f'/api/v1/users/user/{user.pk}/', headers=client.headers)
    assert delete.status_code == 403


@pytest.mark.django_db(transaction=True)
def test_dict_data_is_not_a_route(sample_app):
    """
    `GET /{item_id}/dict_data/` of a UserRouteBase route answered staff all the attributes of
    the item, past the schema of the route: it is not a route any more.
    """
    from entity.models import ParentEntity

    staff = get_user_model().objects.create_user('staff', password='weak_password_5', is_staff=True)
    client = get_api_client(sample_app, staff.jwt_build(auth_type='password'))
    item = ParentEntity.objects.create(name='Parent')

    assert client.get(f'{ENTITY}/parent_entity/{item.pk}/').status_code == 200
    assert client.get(f'{ENTITY}/parent_entity/{item.pk}/dict_data/').status_code == 404


class ProbeBase(UserOpenApiMixin, InitialRouteBase):
    abstract = True

    @http_get('/probe/')
    def action_probe(self, **kwargs):
        pass


def registered_security(route_cls):
    (route,) = route_cls.as_router().routes
    return route.openapi_extra.get('security')


@pytest.mark.parametrize(
    'parent_required, child_required', [(False, True), (True, False), (False, False)]
)
def test_security_does_not_depend_on_registration_order(parent_required, child_required):
    """
    A subclass declared after its parent registered its routes (as_router) gets the security
    of its own `auth_required`, not the one the parent added, and the parent keeps its own.
    """

    class Parent(ProbeBase):
        auth_required = parent_required

    parent_security = registered_security(Parent)

    class Child(Parent):
        auth_required = child_required

    expected = {False: [{}], True: None}
    assert registered_security(Child) == expected[child_required]
    assert registered_security(Parent) == parent_security == expected[parent_required]
