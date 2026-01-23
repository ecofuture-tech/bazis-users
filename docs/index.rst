.. toctree::
   :hidden:

   Home page <self>
   structure


Bazis User
====================================

The package provides extended capabilities for working with users.

bazis/contrib/users/models_abstract.py
------------------

bazis.contrib.users.models_abstract.UserAbstract - abstract user model that implements methods required for extended work with Bazis:
get_full_name
jwt_build
find_or_create
raw_password

bazis.contrib.users.models_abstract.AnonymousUserAbstract - abstract anonymous user model that implements methods required for extended work with Bazis:
- get_full_name

UserMixin - mixin for entity models that can be associated with a user:
- user is stored in the context variable CTX_USER_REQUEST


bazis/contrib/users/routes_abstract.py
----------------------

UserRouteBase - base class for routes associated with users:


bazis/contrib/users/routes.py - routes for working with user functionality:
- token_auth - basic token authentication (JWT), applied in swagger
- UserRouteSet - base route class for working with users

bazis/contrib/users/services.py
-----------------------------

bazis/contrib/users/services.py - services for working with users:
- get_token_data
- get_user_from_token
- get_user_required
- get_user_optional