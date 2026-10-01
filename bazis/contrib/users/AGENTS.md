# bazis-users — guide for AI agents

Users and authentication by session JWT for Bazis: the user model, the token endpoint,
and the route base classes that know the current user. Use it whenever an API has users;
bazis-permit (permissions) and bazis-authing (login flows) build on it.

## Setup

1. A project app with the user model (the package does not create the table itself):

   ```python
   # users/models.py
   from bazis.contrib.users.models_abstract import AnonymousUserAbstract, UserAbstract
   from bazis.core.models_abstract import JsonApiMixin, UuidMixin

   class User(JsonApiMixin, UuidMixin, UserAbstract):
       pass

   class AnonymousUser(AnonymousUserAbstract):
       pass

   # users/apps.py
   from bazis.contrib.users.apps import UsersConfig as UsersConfigBase

   class UsersConfig(UsersConfigBase):
       name = 'users'
   ```

2. `BS_INSTALLED_APPS='["users", ...]'`, `BS_AUTH_USER_MODEL=users.User`,
   `BS_AUTH_ANONYMOUS_USER_MODEL=users.models.AnonymousUser`.
3. Optionally register the user routes: `router.register('bazis.contrib.users.router')`
   (`/user/`). With them a user sees and changes only himself, staff create, list and
   delete users, and only a superuser changes `is_staff`, `is_superuser`, `is_active`.
   Projects with bazis-permit protect users with a `PermitRouteBase` route instead.

## Authentication

- `POST BAZIS_OPENAPI_TOKEN_URL` (default `/api/openapi-token/`, OAuth2 password form)
  returns `{"access_token": ..., "token_type": "bearer"}`; Swagger uses it.
- The token is read from `Authorization: Bearer`, or the query parameter or the cookie
  named `BAZIS_AUTH_COOKIE_NAME` (default `bazis_auth`). It is an HMAC JWT signed with
  `SECRET_KEY` with `sub` (username), `iat` and `exp` (`BAZIS_JWT_SESSION_LIFETIME`
  seconds). A token without
  `exp` is anonymous; an expired or invalid token is 401.
- `user.jwt_build()` builds a token (e.g. after a custom login).

## Routes

- `UserRouteBase` (`bazis.contrib.users.routes_abstract`): `self.inject.user` is the user
  or the anonymous user; the filter context gets `_user`. Base class for routes that need
  the user (bazis-permit routes extend it).
- `UserRequiredRouteBase`: the same, for routes that require authentication.
- FastAPI dependencies in `bazis.contrib.users.service`: `get_user_optional`,
  `get_user_required`, `get_token_data`.

## Rules

- A user must never be able to change his own groups, permissions or staff flags: keep
  those fields out of the update schemas of custom user routes, or check them in
  `hook_after_update` as `UserRouteSet` does.
- Check `bazis_doctor` after changing the user model (`users.E001`).
