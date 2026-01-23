from django.utils.translation import gettext_lazy as _

from bazis.core.routing import BazisRouter

from .routes import UserRouteSet


router = BazisRouter(tags=[_('Users')])
router.register('/user', UserRouteSet.as_router())
