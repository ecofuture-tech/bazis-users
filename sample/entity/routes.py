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
