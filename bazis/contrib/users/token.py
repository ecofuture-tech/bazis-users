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

from starlette.status import HTTP_401_UNAUTHORIZED

from bazis.core.app import app
from bazis.core.errors import SchemaErrors

from .schemas import TokenResponse
from .service import token_auth


app.post(
    settings.BAZIS_OPENAPI_TOKEN_URL,
    response_model=TokenResponse,
    responses={HTTP_401_UNAUTHORIZED: {'model': SchemaErrors}},
)(token_auth)
