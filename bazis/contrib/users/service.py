from django.conf import settings
from django.utils.translation import gettext_lazy as _

from fastapi import Cookie, Depends, HTTPException, Query
from fastapi.security import OAuth2PasswordBearer

from starlette.status import HTTP_401_UNAUTHORIZED

from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError

from bazis.core.errors import JsonApi401Exception

from . import get_anonymous_user_model, get_user_model


User = get_user_model() # noqa: N806
AnonymousUser = get_anonymous_user_model()


def get_token_data(
    token_header: str = Depends(
        OAuth2PasswordBearer(tokenUrl=settings.BAZIS_OPENAPI_TOKEN_URL, auto_error=False)
    ),
    token_param: str | None = Query(default=None, alias=settings.BAZIS_AUTH_COOKIE_NAME),
    token_cookie: str | None = Cookie(default=None, alias=settings.BAZIS_AUTH_COOKIE_NAME),
) -> dict:
    """
    Decodes the JWT token provided by the client. If the token is missing or
    invalid, returns an empty dictionary. Raises a JsonApi401Exception if the token
    has expired.
    """
    token = token_param or token_header or token_cookie

    if not token:
        return {}
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.BAZIS_JWT_SESSION_ALG])
    except ExpiredSignatureError:
        raise JsonApi401Exception(detail=str(_('Token has expired'))) from None
    except JWTError:
        raise JsonApi401Exception(detail=str(_('Token is invalid'))) from None


def get_user_from_token(token_data: dict = Depends(get_token_data)) -> User | None:
    """
    Retrieves the user associated with the given token data. Returns None if the
    token data is empty or invalid.
    """
    if not token_data:
        return
    if user := User.get_with_cache(username=token_data.get('sub'), ttl=10):
        if user.is_active:
            return user


def get_user_required(user: User = Depends(get_user_from_token)) -> User:
    """
    Ensures that a valid user is retrieved from the token. Raises an HTTP 401
    Unauthorized exception if the user is not found or the token is invalid.
    """
    if not user:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail=_('Token is invalid'),
            headers={'WWW-Authenticate': 'Bearer'},
        )
    return user


def get_user_optional(user: User = Depends(get_user_from_token)) -> User | AnonymousUser:
    """
    Retrieves the user associated with the given token. If the user is not found,
    returns an AnonymousUser instance instead.
    """
    if not user:
        return AnonymousUser()
    return user
