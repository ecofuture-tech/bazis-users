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

from fastapi import Depends

from starlette.status import HTTP_401_UNAUTHORIZED

from bazis.core.errors import SchemaErrors
from bazis.core.routes_abstract.initial import inject_make
from bazis.core.routes_abstract.jsonapi import JsonapiRouteBase
from bazis.core.utils.functools import get_attr

from . import get_anonymous_user_model, get_user_model
from .models_abstract import UserMixin
from .service import get_user_optional, get_user_required


User = get_user_model() # noqa: N806
AnonymousUser = get_anonymous_user_model()


class UserOpenApiMixin:
    """
    OpenAPI of the routes that read the token (`get_user_optional`, `get_user_required`):
    the 401 response, and the security requirement for a client generator: the token is
    optional unless `auth_required`. FastAPI emits the requirement of the token
    (`OAuth2PasswordBearer`) for every such route as if it were mandatory; the empty
    requirement added here makes a route that serves anonymous requests say so.
    """

    #: the routes fail a request without a valid token (otherwise it is anonymous)
    auth_required: bool = False

    @classmethod
    def route_responses(cls, route_ctx):
        """
        An invalid or expired token is 401 for every route, a missing one also if
        `auth_required`.
        """
        return {**super().route_responses(route_ctx), HTTP_401_UNAUTHORIZED: {'model': SchemaErrors}}

    @classmethod
    def route_openapi_extra(cls, route_ctx):
        """
        An optional token is declared as `security: [..., {}]` (added to the requirement
        of FastAPI).
        """
        extra = super().route_openapi_extra(route_ctx)
        if not cls.auth_required:
            extra['security'] = [{}]
        return extra


class UserRouteBase(UserOpenApiMixin, JsonapiRouteBase):
    """
    Base class for user-related routes, providing common functionality and user
    injection mechanisms.
    """

    abstract: bool = True

    @inject_make()
    class InjectUser:
        """
        Inner class to handle user injection, allowing for both authenticated and
        anonymous users.
        """

        user: User | AnonymousUser = Depends(get_user_optional)

    def __init__(self, *args, **kwargs):
        """
        Initializes the UserRouteBase, setting the user context and calling the parent
        class initializer.
        """
        self._set_user(kwargs['inject'].user)
        super().__init__(*args, **kwargs)

    def _set_user(self, user):
        """
        Sets the user context for the current request if the user is authenticated (not
        anonymous).
        """
        if user and getattr(user, 'is_anonymous', None) is False:
            UserMixin.CTX_USER_REQUEST.set(user)

    def route_run(self, *args, **kwargs):
        """
        Executes the route, ensuring the user context is set before calling the parent
        class's route_run method.
        """
        self._set_user(self.inject.user)
        return super().route_run(*args, **kwargs)

    @classmethod
    def get_fiter_context(cls, route: 'JsonapiRouteBase' = None, **kwargs):
        """
        Generates the filter context for the route, incorporating user-specific filters
        if available.
        """
        user = get_attr(kwargs, 'user') or get_attr(route, 'inject.user')
        return super().get_fiter_context(route=route) | {
            '_user': get_attr(user, 'id'),
        }


class UserRequiredRouteBase(UserRouteBase):
    """
    Base class for routes that require an authenticated user, extending
    UserRouteBase.
    """

    abstract: bool = True
    auth_required: bool = True

    @inject_make()
    class InjectUser:
        """
        Inner class to handle user injection, ensuring that only authenticated users are
        injected.
        """

        user: User = Depends(get_user_required)
