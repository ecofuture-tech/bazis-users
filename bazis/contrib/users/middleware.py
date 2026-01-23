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

from .models_abstract import UserMixin


class UserRequestMiddleware:
    """
    Middleware that attaches the current authenticated user to the context for the
    duration of the request.
    """

    def __init__(self, get_response):
        """
        Initializes the middleware with the given response handler.
        """
        self.get_response = get_response

    def __call__(self, request):
        """
        Processes the incoming request, setting the user in the context if the user is
        authenticated, and then passes the request to the next middleware or view.
        """
        if request.user and getattr(request.user, 'is_anonymous', None) is False:
            UserMixin.CTX_USER_REQUEST.set(request.user)
        return self.get_response(request)
