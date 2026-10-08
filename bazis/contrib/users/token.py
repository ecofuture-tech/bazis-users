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
The token endpoint, `POST BAZIS_OPENAPI_TOKEN_URL`: the login of Swagger and of the clients
(OAuth2 password form). It is a route of the application, not of the API router (its path
is absolute), so importing this module declares it: the router module of the project
(`BS_BAZIS_ROUTER_MODULE`) imports it, directly or through `bazis.contrib.users.router`
(`users.E002` reports a project where it is missing).
"""

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.signals import user_logged_in
from django.utils.translation import gettext_lazy as _

from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm

from starlette.status import HTTP_401_UNAUTHORIZED

from bazis.core.app import app
from bazis.core.errors import SchemaErrors

from .schemas import TokenResponse


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
