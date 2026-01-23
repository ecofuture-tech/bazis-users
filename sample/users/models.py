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

from bazis.contrib.users.models_abstract import AnonymousUserAbstract, UserAbstract
from bazis.core.models_abstract import JsonApiMixin, UuidMixin


class User(JsonApiMixin, UuidMixin, UserAbstract):
    """
    Represents a user in the system, combining JSON API support, UUID functionality,
    and user-specific attributes and methods.
    """

    pass


class AnonymousUser(AnonymousUserAbstract):
    """
    Represents an anonymous user with attributes and methods specific to users who
    are not logged in.
    """

    pass
