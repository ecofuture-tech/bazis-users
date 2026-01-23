from django.utils.translation import gettext_lazy as _


class UserAdminAbstract:

    def get_fields_common(self, request, obj=None):
        return ('username', 'password')

    def get_fields_personal(self, request, obj=None):
        return ('first_name', 'last_name', 'email')

    def get_fields_permissions(self, request, obj=None):
        return ('is_active', 'is_staff', 'is_superuser')

    def get_fields_dates(self, request, obj=None):
        return ('last_login', 'date_joined', 'dt_first_login')

    def get_fieldsets(self, request, obj=None):
        if not obj:
            return self.add_fieldsets
        return (
            (None, {'fields': self.get_fields_common(request, obj)}),
            (_('Personal info'), {'fields': self.get_fields_personal(request, obj)}),
            (_('Permissions'), {'fields': self.get_fields_permissions(request, obj)}),
            (_('Important dates'), {'fields': self.get_fields_dates(request, obj)}),
        )
