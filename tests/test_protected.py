from django.apps import apps

import pytest
from bazis_test_utils.utils import get_api_client

from bazis.contrib.users import get_user_model


@pytest.mark.django_db(transaction=True)
def test_protected(sample_app):
    """
    Test the API endpoints for both protected and non-protected routes. This
    function verifies the behavior of the endpoints when accessed with and without
    user authentication. It ensures that non-protected routes are accessible without
    authentication and protected routes require authentication.
    """
    User = get_user_model() # noqa: N806
    user_1 = User.objects.create_user('user1', email='user1@site.com', password='weak_password_2')

    #############################
    # Test with no user for non-protected route
    #############################

    response = get_api_client(sample_app).post(
        '/api/v1/entity/parent_entity/',
        json_data={
            'data': {
                'type': 'entity.parent_entity',
                'bs:action': 'add',
                'attributes': {
                    'name': 'Test name',
                    'description': 'Test description',
                    'is_active': True,
                    'price': '100.49',
                    'dt_approved': '2024-01-12T16:54:12Z',
                },
            },
        },
    )

    assert response.status_code == 201
    assert (
        apps.get_model('entity.ParentEntity')
        .objects.filter(pk=response.json()['data']['id'])
        .exists()
    )

    #############################
    # Test with user for non-protected route
    #############################

    response = get_api_client(sample_app, user_1.jwt_build()).post(
        '/api/v1/entity/parent_entity/',
        json_data={
            'data': {
                'type': 'entity.parent_entity',
                'bs:action': 'add',
                'attributes': {
                    'name': 'Test name',
                    'description': 'Test description',
                    'is_active': True,
                    'price': '100.49',
                    'dt_approved': '2024-01-12T16:54:12Z',
                },
            },
        },
    )

    assert response.status_code == 201
    assert (
        apps.get_model('entity.ParentEntity')
        .objects.filter(pk=response.json()['data']['id'])
        .exists()
    )

    data = response.json()

    parent_entity_data = data['data']

    #############################
    # Test with no user for protected route
    #############################

    response = get_api_client(sample_app).post(
        '/api/v1/entity/extended_entity/',
        json_data={
            'data': {
                'type': 'entity.extended_entity',
                'bs:action': 'add',
                'attributes': {
                    'extended_name': 'Extended test name',
                    'extended_description': 'Extended test description',
                    'extended_is_active': True,
                    'extended_price': '100.49',
                    'extended_dt_approved': '2024-01-12T16:54:12Z',
                },
                'relationships': {
                    'parent_entity': {
                        'data': {
                            'id': parent_entity_data['id'],
                            'type': 'entity.parent_entity',
                        },
                    },
                },
            },
        },
    )

    assert response.status_code == 401

    #############################
    # Test with user for protected route
    #############################

    response = get_api_client(sample_app, user_1.jwt_build()).post(
        '/api/v1/entity/extended_entity/',
        json_data={
            'data': {
                'type': 'entity.extended_entity',
                'bs:action': 'add',
                'attributes': {
                    'extended_name': 'Extended test name',
                    'extended_description': 'Extended test description',
                    'extended_is_active': True,
                    'extended_price': '100.49',
                    'extended_dt_approved': '2024-01-12T16:54:12Z',
                },
                'relationships': {
                    'parent_entity': {
                        'data': {
                            'id': parent_entity_data['id'],
                            'type': 'entity.parent_entity',
                        },
                    },
                },
            },
        },
    )

    assert response.status_code == 201
    assert (
        apps.get_model('entity.ExtendedEntity')
        .objects.filter(pk=response.json()['data']['id'])
        .exists()
    )
