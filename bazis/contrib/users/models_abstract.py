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

"""
The module provides mixins for working with User
"""

from contextvars import ContextVar
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import AnonymousUser as BaseAnonymousUser
from django.contrib.auth.signals import user_logged_in
from django.contrib.gis.db import models
from django.db import IntegrityError, transaction
from django.dispatch import receiver
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

import jwt

from bazis.core.errors import JsonApiBazisError, JsonApiBazisException
from bazis.core.models_abstract import InitialBase, JsonApiMixin


class UserAbstract(AbstractUser, InitialBase):
    """
    Abstract base class for user models, extending Django's AbstractUser and
    InitialBase.
    """
    dt_first_login = models.DateTimeField('Date/time of first login', blank=True, null=True)

    class Meta:
        """
        Meta class for UserAbstract, defining verbose names and setting the model as
        abstract.
        """

        verbose_name = _('user')
        verbose_name_plural = _('users')
        abstract = True

    def get_full_name(self):
        """
        Returns the full name of the user, combining first and last name if available,
        otherwise returns the username.
        """
        full_name = ''
        if self.first_name:
            full_name = self.first_name
        if self.last_name:
            full_name += ' ' + self.last_name
        return full_name.strip() or self.username

    def jwt_build(self, auth_type=None) -> str:
        """
        Generates a JSON Web Token (JWT) for the user, optionally including an
        authentication type.
        """
        dt_now = now()
        data = {
            'sub': self.username,
            'iat': dt_now,
            'exp': dt_now + timedelta(seconds=settings.BAZIS_JWT_SESSION_LIFETIME),
        }
        if auth_type:
            data['auth_type'] = auth_type

        return jwt.encode(data, settings.SECRET_KEY, algorithm=settings.BAZIS_JWT_SESSION_ALG)

    @classmethod
    def find_or_create(cls, filters, params):
        """
        Class method to find a user by filters or create a new one with the provided
        parameters, ensuring atomic transactions.
        """
        with transaction.atomic():
            if user := cls.objects.filter(filters).first():
                return user

            try:
                with transaction.atomic(savepoint=False):
                    return cls.objects.create(**params)
            except IntegrityError:
                if user := cls.objects.filter(filters).first():
                    return user
                raise

    @property
    def raw_password(self) -> str | None:
        """
        Property to get the user's password in a masked format or set a new password.
        """
        if self.password:
            return '**********'

    @raw_password.setter
    def raw_password(self, value):
        """
        Property to get the user's password in a masked format or set a new password.
        """
        self.set_password(value)


@receiver(user_logged_in)
def set_dt_first_login(sender, user=None, **kwargs):
    if user and not user.dt_first_login and user.pk:
        type(user).objects.filter(pk=user.pk).update(dt_first_login=now())


def language_choices() -> list[tuple[str, str]]:
    """
    The choices of `UserLanguageMixin.language`: the languages of the project (LANGUAGES).
    A callable, so that the migrations do not depend on the languages of the project.
    """
    return settings.LANGUAGES


def language_code(value: str | None) -> str | None:
    """
    The code of LANGUAGES of a language code (the same code or its base code, `ru` of
    `ru-RU`, case-insensitively); None for None or a blank value. Raises ValueError for a
    language the project does not have.
    """
    if value is None or not value.strip():
        return None
    languages = {code.lower(): code for code, _name in settings.LANGUAGES}
    value = value.strip().lower().replace('_', '-')
    if code := languages.get(value) or languages.get(value.split('-')[0]):
        return code
    raise ValueError(value)


#: the language of a user loaded without it (deferred)
_NOT_LOADED = object()


class UserLanguageMixin(InitialBase):
    """
    The language the user has chosen (`language`): a code of LANGUAGES, None when he has
    chosen none. Opt-in: add it to the user model of the project (and run makemigrations);
    the user model of the package has it. A client (bazis-front) adopts it at a login and
    saves the language of its interface there.
    """

    language = models.CharField(
        _('Language'), max_length=15, null=True, blank=True, default=None, choices=language_choices
    )

    #: the language stored in the database, as loaded (`_NOT_LOADED` when it was deferred);
    #: None for a new user
    _language_stored = None

    class Meta:
        abstract = True

    @classmethod
    def from_db(cls, db, field_names, values, **kwargs):
        instance = super().from_db(db, field_names, values, **kwargs)
        instance._language_stored = instance.__dict__.get('language', _NOT_LOADED)
        return instance

    def refresh_from_db(self, using=None, fields=None, **kwargs):
        super().refresh_from_db(using, fields, **kwargs)
        if (fields is None or 'language' in fields) and 'language' in self.__dict__:
            self._language_stored = self.__dict__['language']

    def save(self, *args, **kwargs):
        """
        A language written (changed and saved) is stored as the code of LANGUAGES; another
        language is a validation error of the attribute `language` (422), whatever route
        writes it (the core does not validate the choices). A stored language the project
        no longer has stays until it is changed: the other saves (the login, a new
        password) do not check it.
        """
        update_fields = kwargs.get('update_fields')
        written = 'language' in self.__dict__ and (
            update_fields is None or 'language' in update_fields
        )
        if written and self.language != self._language_stored:
            try:
                self.language = language_code(self.language)
            except ValueError:
                raise JsonApiBazisException(
                    JsonApiBazisError(
                        str(_('The language must be one of: %s'))
                        % ', '.join(code for code, _name in settings.LANGUAGES),
                        loc=('data', 'attributes', 'language'),
                    ),
                    status=422,
                ) from None
        super().save(*args, **kwargs)
        if written:
            self._language_stored = self.language


class AnonymousUserAbstract(BaseAnonymousUser):
    """
    Mixin for the AnonymousUser class, adding basic fields like first_name,
    last_name, and email.
    """

    first_name = ''
    last_name = ''
    email = ''

    def get_full_name(self):
        """
        Returns the full name of the anonymous user, combining first and last name if
        available, otherwise returns the username.
        """
        full_name = ''
        if self.first_name:
            full_name = self.first_name
        if self.last_name:
            full_name += ' ' + self.last_name
        return full_name.strip() or self.username


class UserMixin(JsonApiMixin):
    """
    Mixin that allows saving the current user in the context using a ContextVar.
    """

    #: Context variable in which the current active user can be stored
    CTX_USER_REQUEST: ContextVar['UserMixin'] = ContextVar('CTX_USER_REQUEST', default=None)

    class Meta:
        """
        Meta class for UserMixin, setting the model as abstract.
        """

        abstract = True
