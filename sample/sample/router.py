from bazis.core.routing import BazisRouter


router = BazisRouter(prefix='/api/v1')

router.register('users.router')
router.register('entity.router')
