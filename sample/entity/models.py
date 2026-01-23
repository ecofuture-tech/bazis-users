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

from django.db import models
from django.utils.translation import gettext_lazy as _

from bazis_test_utils.models_abstract import (
    ChildEntityBase,
    DependentEntityBase,
    ExtendedEntityBase,
    ParentEntityBase,
)

from bazis.contrib.users.models_abstract import UserMixin
from bazis.core.models_abstract import DtMixin, JsonApiMixin, UuidMixin


class ChildEntity(UserMixin, DtMixin, UuidMixin, JsonApiMixin, ChildEntityBase):
    """
    Represents a child entity in the system, inheriting common properties and
    methods from various mixins and the ChildEntityBase.
    """

    class Meta:
        """
        Metadata for the ChildEntity model, including singular and plural verbose names
        for better readability in the admin interface.
        """

        verbose_name = _('Child entity')
        verbose_name_plural = _('Child entities')


class DependentEntity(UserMixin, DtMixin, UuidMixin, JsonApiMixin, DependentEntityBase):
    """
    Represents an entity that depends on a parent entity, with a foreign key
    relationship to the ParentEntity model.
    """

    parent_entity = models.ForeignKey(
        'ParentEntity', on_delete=models.CASCADE, related_name='dependent_entities'
    )

    class Meta:
        """
        Metadata for the DependentEntity model, including singular and plural verbose
        names for better readability in the admin interface.
        """

        verbose_name = _('Dependent entity')
        verbose_name_plural = _('Dependent entities')


class ExtendedEntity(UserMixin, DtMixin, UuidMixin, JsonApiMixin, ExtendedEntityBase):
    """
    Represents an extended entity that has a one-to-one relationship with a parent
    entity, inheriting properties from various mixins and the ExtendedEntityBase.
    """

    parent_entity = models.OneToOneField(
        'ParentEntity', on_delete=models.CASCADE, related_name='extended_entity'
    )

    class Meta:
        """
        Metadata for the ExtendedEntity model, including singular and plural verbose
        names for better readability in the admin interface.
        """

        verbose_name = _('Extended entity')
        verbose_name_plural = _('Extended entities')


class ParentEntity(UserMixin, DtMixin, UuidMixin, JsonApiMixin, ParentEntityBase):
    """
    Represents a parent entity in the system, with a many-to-many relationship to
    child entities, inheriting common properties and methods from various mixins and
    the ParentEntityBase.
    """

    child_entities = models.ManyToManyField(
        ChildEntity,
        related_name='parent_entities',
        blank=True,
    )

    class Meta:
        """
        Metadata for the ParentEntity model, including singular and plural verbose names
        for better readability in the admin interface.
        """

        verbose_name = _('Parent entity')
        verbose_name_plural = _('Parent entities')
