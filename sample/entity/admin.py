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

from django.contrib import admin

from bazis.core.admin_abstract import AutocompleteMixin, DtAdminMixin

from .models import ChildEntity, DependentEntity, ExtendedEntity, ParentEntity


@admin.register(ChildEntity)
class ChildEntityAdmin(AutocompleteMixin, DtAdminMixin, admin.ModelAdmin):
    """
    Admin configuration for ChildEntity model, including display, filter, and search
    options.
    """

    list_display = ('id', 'child_name', 'child_is_active')
    list_filter = ('child_is_active',)
    search_fields = ('child_name', 'child_description')


@admin.register(DependentEntity)
class DependentEntityAdmin(AutocompleteMixin, DtAdminMixin, admin.ModelAdmin):
    """
    Admin configuration for DependentEntity model, including display, filter, and
    search options.
    """

    list_display = ('id', 'dependent_name', 'dependent_is_active')
    list_filter = ('dependent_is_active',)
    search_fields = ('dependent_name', 'dependent_description')


@admin.register(ExtendedEntity)
class ExtendedEntityAdmin(AutocompleteMixin, DtAdminMixin, admin.ModelAdmin):
    """
    Admin configuration for ExtendedEntity model, including display, filter, and
    search options.
    """

    list_display = ('id', 'extended_name', 'extended_is_active')
    list_filter = ('extended_is_active',)
    search_fields = ('extended_name', 'extended_description')


class ChildEntityInline(AutocompleteMixin, admin.TabularInline):
    """
    Inline configuration for ChildEntity model in the ParentEntity admin interface.
    """

    model = ParentEntity.child_entities.through
    extra = 0


class DependentEntityInline(AutocompleteMixin, admin.TabularInline):
    """
    Inline configuration for DependentEntity model in the ParentEntity admin
    interface.
    """

    model = DependentEntity
    extra = 0


class ExtendedEntityInline(AutocompleteMixin, admin.TabularInline):
    """
    Inline configuration for ExtendedEntity model in the ParentEntity admin
    interface.
    """

    model = ExtendedEntity
    extra = 0


@admin.register(ParentEntity)
class ParentEntityAdmin(AutocompleteMixin, DtAdminMixin, admin.ModelAdmin):
    """
    Admin configuration for ParentEntity model, including display, filter, search
    options, and inlines for related entities.
    """

    list_display = ('id', 'name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    inlines = (ChildEntityInline, DependentEntityInline, ExtendedEntityInline)
