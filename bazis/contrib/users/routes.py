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

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.signals import user_logged_in
from django.utils.translation import gettext_lazy as _

from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm

from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN

from bazis.core.app import app
from bazis.core.errors import JsonApi403Exception, SchemaErrors
from bazis.core.routes_abstract.initial import inject_make
from bazis.core.routes_abstract.jsonapi import JsonapiRouteBase
from bazis.core.schemas import CrudApiAction, SchemaFields, SchemaInclusion, SchemaInclusions
from bazis.core.schemas.enums import RouteKind

from .routes_abstract import UserOpenApiMixin
from .schemas import TokenResponse
from .service import get_user_required


User = get_user_model() # noqa: N806


@app.post(
    settings.BAZIS_OPENAPI_TOKEN_URL,
    response_model=TokenResponse,
    responses={HTTP_401_UNAUTHORIZED: {'model': SchemaErrors}},
)
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


class UserRouteSet(UserOpenApiMixin, JsonapiRouteBase):
    """
    Defines a set of routes for user-related operations, inheriting from
    JsonapiRouteBase. It includes model-specific configurations such as fields and
    inclusions.
    """

    model = User
    auth_required = True

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

    @classmethod
    def route_responses(cls, route_ctx):
        """
        Only staff creates and deletes users and only a superuser changes the privileged
        fields: 403.
        """
        responses = super().route_responses(route_ctx)
        if route_ctx.kind in {RouteKind.CREATE, RouteKind.UPDATE, RouteKind.DELETE}:
            responses[HTTP_403_FORBIDDEN] = {'model': SchemaErrors}
        return responses

    #: the fields only a superuser can set
    privileged_fields = ('is_staff', 'is_superuser', 'is_active')

    def get_queryset(self):
        """
        A user who is not staff sees and changes only himself.
        """
        queryset = super().get_queryset()
        if not self.inject.user.is_staff:
            queryset = queryset.filter(pk=self.inject.user.pk)
        return queryset

    def check_privileged_fields(self, item, before: dict):
        if self.inject.user.is_superuser:
            return
        for field in self.privileged_fields:
            if getattr(item, field) != before[field]:
                raise JsonApi403Exception(detail=str(_('Only a superuser can change %s')) % field)

    def hook_before_create(self, item):
        if not self.inject.user.is_staff:
            raise JsonApi403Exception()
        super().hook_before_create(item)

    def hook_after_create(self, item):
        # inside the transaction: the error rolls the creation back
        super().hook_after_create(item)
        self.check_privileged_fields(
            item, {'is_staff': False, 'is_superuser': False, 'is_active': True}
        )

    def hook_before_update(self, item):
        super().hook_before_update(item)
        # the data is not applied yet
        self._privileged_before = {field: getattr(item, field) for field in self.privileged_fields}

    def hook_after_update(self, item):
        # inside the transaction: the error rolls the change back
        super().hook_after_update(item)
        self.check_privileged_fields(item, self._privileged_before)

    def destroy(self, item_id: str):
        if not self.inject.user.is_staff:
            raise JsonApi403Exception()
        return super().destroy(item_id)

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
