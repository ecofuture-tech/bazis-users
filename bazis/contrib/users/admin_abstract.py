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

from django.utils.translation import gettext_lazy as _


class UserAdminAbstract:

    def get_fields_common(self, request, obj=None):
        return ('username', 'password')

    def get_fields_personal(self, request, obj=None):
        return ('first_name', 'last_name', 'email')

    def get_fields_permissions(self, request, obj=None):
        return ('is_active', 'is_staff', 'is_superuser')

    def get_fields_dates(self, request, obj=None):
        return ('last_login', 'date_joined', 'dt_first_login')

    def get_fieldsets(self, request, obj=None):
        if not obj:
            return self.add_fieldsets
        return (
            (None, {'fields': self.get_fields_common(request, obj)}),
            (_('Personal info'), {'fields': self.get_fields_personal(request, obj)}),
            (_('Permissions'), {'fields': self.get_fields_permissions(request, obj)}),
            (_('Important dates'), {'fields': self.get_fields_dates(request, obj)}),
        )
