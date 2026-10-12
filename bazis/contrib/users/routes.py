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

from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from fastapi import Depends

from starlette.status import HTTP_403_FORBIDDEN

from bazis.core.errors import JsonApi403Exception, SchemaErrors
from bazis.core.routes_abstract.initial import inject_make
from bazis.core.routes_abstract.jsonapi import JsonapiRouteBase
from bazis.core.schemas import (
    CrudAccessAction,
    CrudApiAction,
    SchemaFields,
    SchemaInclusion,
    SchemaInclusions,
)
from bazis.core.schemas.enums import RouteKind

from .models_abstract import UserMixin
from .routes_abstract import UserOpenApiMixin
from .service import get_user_required

# importing the module declares the token endpoint on the application with the user
# routes; the name `token_auth` stays importable from here for the projects written for
# bazis-users < 2.6.1: remove the name in 3.0 and keep the import of the module
from .token import token_auth  # noqa: F401


User = get_user_model() # noqa: N806


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

    @classmethod
    def restrict_queryset(cls, qs, access_action, user=None, **kwargs):
        """
        The users a user sees and changes: staff every user, another authenticated user
        only himself, nobody without authentication. The route's own list and items, and
        for the other routes the users their relationships link (403 `ERR_RELATION_ACCESS`
        for another one), their `included` and their filters through a relation (the core
        calls it on the class of the default route of the user model). Without a user (a
        route that has none) the authenticated user of the request
        (`UserMixin.CTX_USER_REQUEST`). Never raises. A subclass whose users pick other
        users widens it for `CrudAccessAction.VIEW` only and calls `super()` otherwise: a
        reverse relation to the users changes the users it links (`change`).
        """
        if (user := UserMixin.authenticated_user(user)) is None:
            return qs.none()
        if user.is_staff:
            return qs
        return qs.filter(pk=user.pk)

    def get_queryset(self):
        """
        A user who is not staff sees and changes only himself: the rule of
        `UserRouteSet.restrict_queryset`, also in a subclass that overrides it (a project
        whose users pick other users widens what the other routes show and link for
        `view`, not who changes a user).
        """
        return UserRouteSet.restrict_queryset(
            super().get_queryset(), CrudAccessAction.VIEW, user=self.inject.user
        )

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
