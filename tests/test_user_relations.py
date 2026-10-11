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
The users of the other routes (`UserRouteSet.restrict_queryset`, the rule of the user
routes): a user who is not staff links only himself into a relationship to the users, sees
only himself in `included` and filters only by himself through a relation; staff every user;
an anonymous user nobody.
"""

import pytest
from bazis_test_utils.utils import get_api_client
from entity.models import ParentEntity

from bazis.contrib.users import get_anonymous_user_model, get_user_model
from bazis.contrib.users.models_abstract import UserMixin
from bazis.core.schemas import CrudAccessAction


User = get_user_model()

URL_PARENT = '/api/v1/entity/parent_entity/'


@pytest.fixture
def people():
    staff = User.objects.create_user('staff', password='weak_password_2', is_staff=True)
    user = User.objects.create_user('user', password='weak_password_3')
    other = User.objects.create_user('other', password='weak_password_4')
    return staff, user, other


def linkage(*users) -> dict:
    return {'data': [{'id': str(it.id), 'type': 'users.user'} for it in users]}


def create(client, *users):
    return client.post(
        URL_PARENT,
        json_data={
            'data': {
                'type': 'entity.parent_entity',
                'bs:action': 'add',
                'attributes': {'name': 'Parent'},
                'relationships': {'watchers': linkage(*users)},
            }
        },
    )


@pytest.mark.django_db(transaction=True)
def test_user_links_only_himself(sample_app, people):
    staff, user, other = people
    client = get_api_client(sample_app, user.jwt_build())

    response = create(client, other)
    assert response.status_code == 403, response.text
    [error] = response.json()['errors']
    assert error['code'] == 'ERR_RELATION_ACCESS'
    assert error['source']['pointer'] == '/data/relationships/watchers'
    assert not ParentEntity.objects.exists()

    response = create(client, user)
    assert response.status_code == 201, response.text
    parent = ParentEntity.objects.get()
    assert list(parent.watchers.all()) == [user]

    # the relationships endpoint and an update refuse another user too
    response = client.post(
        f'{URL_PARENT}{parent.id}/relationships/watchers', json_data=linkage(other)
    )
    assert response.status_code == 403, response.text
    assert response.json()['errors'][0]['code'] == 'ERR_RELATION_ACCESS'
    response = client.patch(
        f'{URL_PARENT}{parent.id}/',
        json_data={
            'data': {
                'id': str(parent.id),
                'type': 'entity.parent_entity',
                'bs:action': 'change',
                'relationships': {'watchers': linkage(user, other)},
            }
        },
    )
    assert response.status_code == 403, response.text
    assert list(parent.watchers.all()) == [user]


@pytest.mark.django_db(transaction=True)
def test_staff_links_any_user(sample_app, people):
    staff, user, other = people
    response = create(get_api_client(sample_app, staff.jwt_build()), user, other)
    assert response.status_code == 201, response.text
    assert set(ParentEntity.objects.get().watchers.all()) == {user, other}


@pytest.mark.django_db(transaction=True)
def test_anonymous_links_nobody(sample_app, people):
    __, user, __ = people
    response = create(get_api_client(sample_app), user)
    assert response.status_code == 403, response.text
    assert response.json()['errors'][0]['code'] == 'ERR_RELATION_ACCESS'


@pytest.mark.django_db(transaction=True)
def test_a_relationship_unchanged_keeps_the_users_the_user_does_not_see(sample_app, people):
    """Only the users whose link changes are checked: the others stay linked."""
    staff, user, other = people
    parent = ParentEntity.objects.create(name='Parent')
    parent.watchers.add(user, other)
    client = get_api_client(sample_app, user.jwt_build())

    response = client.patch(
        f'{URL_PARENT}{parent.id}/',
        json_data={
            'data': {
                'id': str(parent.id),
                'type': 'entity.parent_entity',
                'bs:action': 'change',
                'relationships': {'watchers': linkage(user, other)},
            }
        },
    )
    assert response.status_code == 200, response.text
    assert set(parent.watchers.all()) == {user, other}

    # unlinking a user is not a link: allowed
    response = client.client.request(
        'DELETE',
        f'{URL_PARENT}{parent.id}/relationships/watchers',
        json=linkage(other),
        headers=client.headers,
    )
    assert response.status_code in (200, 204), response.text
    assert list(parent.watchers.all()) == [user]


@pytest.mark.django_db(transaction=True)
def test_included_and_filters_show_only_the_users_the_user_sees(sample_app, people):
    staff, user, other = people
    parent = ParentEntity.objects.create(name='Parent')
    parent.watchers.add(user, other)

    def included(actor) -> set[str]:
        response = get_api_client(sample_app, actor.jwt_build()).get(
            f'{URL_PARENT}{parent.id}/', params={'include': 'watchers'}
        )
        assert response.status_code == 200, response.text
        # the relationship keeps the identifiers of every user
        assert {it['id'] for it in response.json()['data']['relationships']['watchers']['data']} == {
            str(user.id), str(other.id)
        }
        return {it['id'] for it in response.json().get('included', []) if it['type'] == 'users.user'}

    assert included(user) == {str(user.id)}
    assert included(staff) == {str(user.id), str(other.id)}

    def found(actor, username: str) -> list[str]:
        response = get_api_client(sample_app, actor.jwt_build()).get(
            URL_PARENT, params={'filter': f'watchers__username={username}'}
        )
        assert response.status_code == 200, response.text
        return [it['id'] for it in response.json()['data']]

    assert found(user, 'other') == []
    assert found(user, 'user') == [str(parent.id)]
    assert found(staff, 'other') == [str(parent.id)]


@pytest.mark.django_db(transaction=True)
def test_restrict_queryset_without_a_user(people):
    """
    The core calls it on the class with the user of the calling route: None (a route
    without a user) is the user of the request, else nobody; an anonymous user sees nobody.
    """
    from bazis.contrib.users.routes import UserRouteSet

    staff, user, __ = people
    qs = User.objects.all()

    assert not UserRouteSet.restrict_queryset(qs, CrudAccessAction.VIEW).exists()
    assert not UserRouteSet.restrict_queryset(
        qs, CrudAccessAction.VIEW, user=get_anonymous_user_model()(), link=True
    ).exists()

    token = UserMixin.CTX_USER_REQUEST.set(user)
    try:
        assert list(UserRouteSet.restrict_queryset(qs, CrudAccessAction.CHANGE)) == [user]
    finally:
        UserMixin.CTX_USER_REQUEST.reset(token)
    assert UserRouteSet.restrict_queryset(qs, CrudAccessAction.VIEW, user=staff).count() == 3
    assert list(
        UserRouteSet.restrict_queryset(qs, CrudAccessAction.VIEW, user=user, link=True)
    ) == [user]
