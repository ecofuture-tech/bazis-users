# bazis-users — guide for AI agents

Users and authentication by session JWT for Bazis: the user model, the token endpoint,
and the route base classes that know the current user. Use it whenever an API has users;
bazis-permit (permissions) and bazis-authing (login flows) build on it.

### The sections

Read a section with `package_guide("bazis-users", "<section>")` when the step at hand
needs it; `guide_search` finds the part of a section that answers a question. Every
project with users needs Setup and Rules.

| Section | Read it when |
|---|---|
| Setup | you add the user model, the settings, the token endpoint, the user routes and the admin; the fields of a user (`get_full_name`); a foreign key of the user to a model of the project (a migration cycle) |
| Authentication | a client logs in: the token endpoint, where the token is read, the JWT, `jwt_build`, the OpenAPI security |
| Routes | a route needs the current user: `UserRouteBase`, `UserRequiredRouteBase`, the FastAPI dependencies |
| The language of a user | the users choose their language: `UserLanguageMixin`, its route, bazis-front, the work done outside the requests |
| Rules | before you write the code, once: the fields a user must never change himself, the checks `users.E001`, `users.E002` |

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
   `BS_AUTH_ANONYMOUS_USER_MODEL=users.models.AnonymousUser`. The core declares
   `AUTH_USER_MODEL` (default `auth.User`) and the package does not default it to the users
   app (its settings are loaded in every project where it is installed, also in projects
   without the users app): without `BS_AUTH_USER_MODEL` Django keeps `auth.User` and
   `bazis_doctor` reports `users.E001`. Needs bazis 2.5.0 or newer.
3. Register the login, the token endpoint (below), in the router module of the project
   (`BS_BAZIS_ROUTER_MODULE`). It is a route of the application with an absolute path, not
   of the API router, so it is declared by importing its module:

   ```python
   import bazis.contrib.users.token  # noqa: F401  POST BAZIS_OPENAPI_TOKEN_URL
   from bazis.core.routing import BazisRouter

   router = BazisRouter(prefix='/api/v1')
   ```

   Registering the user routes (step 4) imports it too. Without it nobody can log in;
   `bazis_doctor` reports `users.E002`.
4. Optionally register the user routes: `router.register('bazis.contrib.users.router')`
   (`/user/`). With them a user sees and changes only himself, staff create, list and
   delete users, and only a superuser changes `is_staff`, `is_superuser`, `is_active`.
   The same rule is the visibility of the users for the other routes (`restrict_queryset`
   of `UserRouteSet`, bazis-users 2.9): a relationship of a user who is not staff links
   only himself (another user is 403 `ERR_RELATION_ACCESS`), `included` and the filters
   through a relation reach only him. A project whose users pick other users (assignees,
   watchers) subclasses `UserRouteSet` with `default_route = True` and widens
   `restrict_queryset` for `view` only; any other operation goes to `super()`: a reverse
   relation to the users (`Role.users` for `User.roles`, `Team.members` for a foreign key
   of the user) changes the users it links and is checked with `change`, so a widened
   `change` would let a user rewrite the relations of other users:

   ```python
   from bazis.contrib.users.routes import UserRouteSet as UserRouteSetBase
   from bazis.core.schemas import CrudAccessAction

   class UserRouteSet(UserRouteSetBase):
       default_route = True

       @classmethod
       def restrict_queryset(cls, qs, access_action, user=None, **kwargs):
           if access_action == CrudAccessAction.VIEW and getattr(user, 'is_authenticated', False):
               return qs  # every user may be picked
           return super().restrict_queryset(qs, access_action, user=user, **kwargs)
   ```

   It never raises (`user` may be None or anonymous). The user routes keep the rule above
   for their own list and items. Projects with bazis-permit protect users with a
   `PermitRouteBase` route instead (keep the import of step 3).
5. The admin of the users: `UserAdminAbstract` (`bazis.contrib.users.admin_abstract`)
   before the `UserAdmin` of Django; with bazis-permit, `UserPermitAdminMixin`
   (`bazis.contrib.permit.admin_abstract`: the roles) first:

   ```python
   # users/admin.py
   from django.contrib import admin
   from django.contrib.auth import get_user_model
   from django.contrib.auth.admin import UserAdmin
   from bazis.contrib.permit.admin_abstract import UserPermitAdminMixin  # with bazis-permit
   from bazis.contrib.users.admin_abstract import UserAdminAbstract

   @admin.register(get_user_model())
   class UserAdmin(UserPermitAdminMixin, UserAdminAbstract, UserAdmin):
       pass
   ```

### The fields of a user

`UserAbstract` is the `AbstractUser` of Django (`username`, `first_name`, `last_name`,
`email`, `is_active`, `is_staff`, `is_superuser`, `date_joined`, `last_login`, the groups
and permissions of Django) with `dt_first_login`. The name to show: `get_full_name()`, the
first and the last name, else the username.

### A foreign key of the user to a model of the project

A user model with a foreign key to a model of another app of the project
(`User.department = models.ForeignKey('org.Department', ...)`) makes the first migration
of the users app depend on that app. When the migrations of that app depend on a package
whose migrations depend on the user model (`settings.AUTH_USER_MODEL`): its models
reference `uploadable.FileUpload` (the file has an author), `bg.Task`, or another model
with an author, the migration graph is a cycle (`users.0001_initial` → `org.0001_initial`
→ `uploadable.0004_fileupload_author` → `users.0001_initial`) and `makemigrations --check`
and `migrate` fail with `CircularDependencyError`. `makemigrations` makes that cycle itself:
it does not see the dependency of the package on the user model.

Put the foreign key in a migration of its own, after the first ones:

1. Comment the field out (only the field: leave `autogen_selectors_fields` and the
   permissions that name it as they are) and run
   `python manage.py makemigrations --skip-checks --noinput` (the users app, that app and
   the others): the first migration of the users app no longer depends on that app.
   `--skip-checks`: without the field the system checks fail (bazis-permit: `permit.E005`
   for a permission that names it as a selector, `users.user.item.view.department`) and
   stop `makemigrations`.
2. Restore the field and run `python manage.py makemigrations users --noinput`:
   `000N_user_...` adds it (with its selector array of bazis-permit) and depends on the
   last migration of that app. `--noinput` answers no to any question of a rename (a
   rename question means that more than the field changed between the two runs: there is
   none here), so no terminal is needed.

`makemigrations --check` is then clean and `migrate` applies the field last. If the
migrations exist already, remove the field and the dependency on the app from the first
migration of the users app by hand and add the `AddField` in a new migration that depends
on the last migration of the users app and on the migration of the app that creates the
model. The same holds for any model of the project that the user references and that
references a model with an author.

## Authentication

- `POST BAZIS_OPENAPI_TOKEN_URL` (default `/api/openapi-token/`, OAuth2 password form,
  declared by `bazis.contrib.users.token`, see Setup) returns
  `{"access_token": ..., "token_type": "bearer"}`; Swagger uses it.
- The token is read from `Authorization: Bearer`, or the query parameter or the cookie
  named `BAZIS_AUTH_COOKIE_NAME` (default `bazis_auth`). It is an HMAC JWT signed with
  `SECRET_KEY` with `sub` (username), `iat` and `exp` (`BAZIS_JWT_SESSION_LIFETIME`
  seconds). A token without
  `exp` is anonymous; an expired or invalid token is 401.
- `user.jwt_build()` builds a token (e.g. after a custom login).
- The OpenAPI schema declares the scheme `OAuth2PasswordBearer` (FastAPI, with the token
  URL) and the `security` of every operation that reads the token: `[{OAuth2PasswordBearer}]`
  where the token is required (`UserRequiredRouteBase`, `UserRouteSet`) and
  `[{OAuth2PasswordBearer}, {}]` where an anonymous request is served (`UserRouteBase`, so
  also the routes of bazis-permit); both document the 401 error (`SchemaErrors`), and the 403 where the routes answer it
  (create/update/delete of `UserRouteSet`). A route
  class of your own that injects `get_user_required` directly sets `auth_required = True`
  and inherits `UserOpenApiMixin` to document the same; other classes need nothing.

## Routes

- `UserRouteBase` (`bazis.contrib.users.routes_abstract`): `self.inject.user` is the user
  or the anonymous user; the filter context gets `_user`. Base class for routes that need
  the user (bazis-permit routes extend it).
- `UserRequiredRouteBase`: the same, for routes that require authentication.
- FastAPI dependencies in `bazis.contrib.users.service`: `get_user_optional`,
  `get_user_required`, `get_token_data`, and `get_request_tokens` (the tokens of the
  request undecoded: `RequestTokens.token` is the one it presents).

## The language of a user

- `UserLanguageMixin` (`bazis.contrib.users.models_abstract`) adds `language`: the language
  the user has chosen, a code of `LANGUAGES`, None when he has chosen none. It is opt-in:
  `UserAbstract` has no such field. To use it, add the mixin to the user model of the
  project and run `makemigrations`:

  ```python
  class User(JsonApiMixin, UuidMixin, UserLanguageMixin, UserAbstract):
      pass
  ```

  The user model of the package (`bazis.contrib.users.models.User`) has it. Its choices are
  a callable (`language_choices`), so a change of `LANGUAGES` needs no migration.
- The user reads and changes it himself: the attribute `language` of the user routes
  (`PATCH /user/{id}/`); a project that routes the users with bazis-permit grants the field.
  Saving stores the code of `LANGUAGES` (`ru` of `ru-RU`, `RU`; blank is None); another
  language is a 422 with the pointer `/data/attributes/language`, whatever route saves it.
  Only a language being written is checked: a stored language the project no longer has
  (removed from `LANGUAGES`) stays until it is changed, and the login and the other saves
  pass.
- bazis-front detects the field (`profile_language` of its contract), adopts it at a login
  and saves the language of its interface there.
- The language of a request is still `?lang` or `Accept-Language` (the `LanguageMiddleware`
  of the core), not the profile. Work done for a user outside his requests (e-mails,
  background tasks) uses `translation.override(user.language or settings.LANGUAGE_CODE)`.

## Rules

- A user must never be able to change his own groups, permissions or staff flags: keep
  those fields out of the update schemas of custom user routes, or check them in
  `hook_after_update` as `UserRouteSet` does.
- `BS_AUTH_USER_MODEL` must be set explicitly in every project with the users app
  (`users.E001` at startup tells so); the label and the name are those of the project's
  user model.
- Check `bazis_doctor` after changing the user model (`users.E001`) and the router of the
  project (`users.E002`, the token endpoint).
