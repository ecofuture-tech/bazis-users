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

from dataclasses import dataclass

from django.conf import settings
from django.utils.translation import gettext_lazy as _

from fastapi import Cookie, Depends, HTTPException, Query
from fastapi.security import OAuth2PasswordBearer

from starlette.status import HTTP_401_UNAUTHORIZED

import jwt

from bazis.core.errors import JsonApi401Exception

from . import get_anonymous_user_model, get_user_model


User = get_user_model() # noqa: N806
AnonymousUser = get_anonymous_user_model()

#: the bearer token of `Authorization`, declared in OpenAPI with the token endpoint
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=settings.BAZIS_OPENAPI_TOKEN_URL, auto_error=False)


def decode_token(token: str) -> dict:
    """
    Decodes and verifies a session JWT built by `UserAbstract.jwt_build`.
    Raises `jwt.ExpiredSignatureError` for an expired token and `jwt.InvalidTokenError`
    for any other invalid token. Tokens without an expiration time or a subject are
    rejected.
    """
    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.BAZIS_JWT_SESSION_ALG],
        # iat is informational: checking it would reject tokens issued by a server whose
        # clock is slightly ahead
        options={'require': ['exp', 'sub'], 'verify_iat': False},
    )


@dataclass(frozen=True)
class RequestTokens:
    """
    The tokens of a request: the bearer token of `Authorization`, the query parameter and
    the cookie named BAZIS_AUTH_COOKIE_NAME. bazis-authing reads its store token from the
    same places.
    """

    header: str | None = None
    param: str | None = None
    cookie: str | None = None

    @property
    def token(self) -> str | None:
        """
        The token the request presents: the query parameter, else the bearer token, else
        the cookie.
        """
        return self.param or self.header or self.cookie


def get_request_tokens(
    token_header: str | None = Depends(oauth2_scheme),
    token_param: str | None = Query(default=None, alias=settings.BAZIS_AUTH_COOKIE_NAME),
    token_cookie: str | None = Cookie(default=None, alias=settings.BAZIS_AUTH_COOKIE_NAME),
) -> RequestTokens:
    """
    The tokens of the request (`RequestTokens`), a FastAPI dependency.
    """
    return RequestTokens(header=token_header, param=token_param, cookie=token_cookie)


def session_token_data(token: str | None) -> dict:
    """
    The data of a session token. An empty dictionary if there is no token or the token is
    not a session token (no expiration). Raises JsonApi401Exception if the token has
    expired or is invalid.
    """
    if not token:
        return {}
    try:
        return decode_token(token)
    except jwt.ExpiredSignatureError:
        raise JsonApi401Exception(detail=str(_('Token has expired'))) from None
    except jwt.MissingRequiredClaimError as exc:
        if exc.claim == 'exp':
            # a token signed with SECRET_KEY but without expiration is not a session token
            # (e.g. the token of the authorization store of bazis-authing, which uses the
            # same cookie): it identifies nobody, the request is anonymous
            return {}
        raise JsonApi401Exception(detail=str(_('Token is invalid'))) from None
    except jwt.InvalidTokenError:
        raise JsonApi401Exception(detail=str(_('Token is invalid'))) from None


# The parameters are those of `get_request_tokens`, not a `RequestTokens` dependency:
# bazis-authing < 2.7 calls this function with the three tokens. In 3.0 it takes
# `tokens: RequestTokens = Depends(get_request_tokens)`.
def get_token_data(
    token_header: str | None = Depends(oauth2_scheme),
    token_param: str | None = Query(default=None, alias=settings.BAZIS_AUTH_COOKIE_NAME),
    token_cookie: str | None = Cookie(default=None, alias=settings.BAZIS_AUTH_COOKIE_NAME),
) -> dict:
    """
    The data of the session token of the request (`session_token_data` of
    `RequestTokens.token`), a FastAPI dependency.
    """
    return session_token_data(
        RequestTokens(header=token_header, param=token_param, cookie=token_cookie).token
    )


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
