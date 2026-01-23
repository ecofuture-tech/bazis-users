from fastapi import Depends

from bazis.core.errors import JsonApi403Exception
from bazis.core.routes_abstract.initial import http_get, inject_make
from bazis.core.routes_abstract.jsonapi import JsonapiRouteBase
from bazis.core.utils.functools import get_attr

from . import get_anonymous_user_model, get_user_model
from .models_abstract import UserMixin
from .service import get_user_optional, get_user_required


User = get_user_model() # noqa: N806
AnonymousUser = get_anonymous_user_model()


class UserRouteBase(JsonapiRouteBase):
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

    @http_get(
        '/{item_id}/dict_data/',
    )
    def action_dict_data(self, item_id: str, **kwargs):
        """
        Handles the HTTP GET request to retrieve the dictionary representation of an item.
        """
        if self.inject.user is None or not self.inject.user.is_staff:
            raise JsonApi403Exception()
        return self.set_item(item_id).dict_data


class UserRequiredRouteBase(UserRouteBase):
    """
    Base class for routes that require an authenticated user, extending
    UserRouteBase.
    """

    abstract: bool = True

    @inject_make()
    class InjectUser:
        """
        Inner class to handle user injection, ensuring that only authenticated users are
        injected.
        """

        user: User = Depends(get_user_required)
