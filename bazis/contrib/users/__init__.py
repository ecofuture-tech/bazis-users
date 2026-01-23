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

try:
    from importlib.metadata import PackageNotFoundError, version
    __version__ = version('bazis-users')
except PackageNotFoundError:
    __version__ = 'dev'

from django.conf import settings
from django.contrib.auth import get_user_model

from bazis.core.utils.imp import import_class


def get_anonymous_user_model():
    """
    Retrieve the anonymous user model class specified in the Django settings.
    """
    return import_class(settings.AUTH_ANONYMOUS_USER_MODEL)
