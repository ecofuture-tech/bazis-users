from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.signals import user_logged_in
from django.utils.translation import gettext_lazy as _

from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm

from starlette.status import HTTP_401_UNAUTHORIZED

from bazis.core.app import app
from bazis.core.routes_abstract.initial import inject_make
from bazis.core.routes_abstract.jsonapi import JsonapiRouteBase
from bazis.core.schemas import CrudApiAction, SchemaFields, SchemaInclusion, SchemaInclusions

from .schemas import TokenResponse
from .service import get_user_required


User = get_user_model() # noqa: N806


@app.post(settings.BAZIS_OPENAPI_TOKEN_URL, response_model=TokenResponse)
def token_auth(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Handles user authentication by verifying credentials and generating a JWT token.
    If authentication fails, raises an HTTP 401 Unauthorized exception.
    """
    if not (user := authenticate(username=form_data.username, password=form_data.password)):
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail=_('Credentials are invalid'),
            headers={'WWW-Authenticate': 'Bearer'},
        )
    user_logged_in.send(sender=user.__class__, request=request, user=user)
    return {'access_token': user.jwt_build(auth_type='password'), 'token_type': 'bearer'}


class UserRouteSet(JsonapiRouteBase):
    """
    Defines a set of routes for user-related operations, inheriting from
    JsonapiRouteBase. It includes model-specific configurations such as fields and
    inclusions.
    """

    model = User

    @inject_make()
    class InjectUser:
        """
        Inner class responsible for injecting authenticated user dependencies into the
        route set using the get_user_required service.
        """

        user: User = Depends(get_user_required)

    fields = {
        None: SchemaFields(
            include={
                'raw_password': None,
            },
            exclude={
                'password': None,
                'groups': None,
                'user_permissions': None,
            },
        ),
    }

    inclusions = {
        CrudApiAction.RETRIEVE: SchemaInclusions(
            origin={
                'roles': SchemaInclusion(
                    fields_struct=SchemaFields(
                        origin={
                            'name': None,
                            'slug': None,
                        }
                    )
                ),
            }
        )
    }
