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

from django.apps import apps

from bazis.contrib.users.routes_abstract import UserRequiredRouteBase, UserRouteBase
from bazis.core.schemas import SchemaFields


class ChildEntityRouteSet(UserRouteBase):
    """
    Defines a route set for the ChildEntity model, including schema fields for
    parent entities.
    """

    model = apps.get_model('entity.ChildEntity')

    fields = {
        None: SchemaFields(
            include={
                'parent_entities': None,
            },
        ),
    }


class DependentEntityRouteSet(UserRouteBase):
    """
    Defines a route set for the DependentEntity model.
    """

    model = apps.get_model('entity.DependentEntity')


class ExtendedEntityRouteSet(UserRequiredRouteBase):
    """
    Defines a route set for the ExtendedEntity model, requiring user authentication.
    """

    model = apps.get_model('entity.ExtendedEntity')


class ParentEntityRouteSet(UserRouteBase):
    """
    Defines a route set for the ParentEntity model, including schema fields for
    extended entities and dependent entities.
    """

    model = apps.get_model('entity.ParentEntity')

    # add fields (extended_entity, dependent_entities) to schema
    fields = {
        None: SchemaFields(
            include={'extended_entity': None, 'dependent_entities': None},
        ),
    }
