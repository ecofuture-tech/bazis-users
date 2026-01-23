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

from jose import jwt

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
        data = {
            'sub': self.username,
            'exp': now() + timedelta(seconds=settings.BAZIS_JWT_SESSION_LIFETIME),
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
