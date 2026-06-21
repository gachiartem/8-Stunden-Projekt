from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser

    list_display = (
        'email',
        'first_name',
        'last_name',
        'phone',
        'city',
        'province',
        'is_staff',
        'is_active',
    )

    list_filter = (
        'is_staff',
        'is_active',
        'city',
        'province',
    )

    search_fields = (
        'email',
        'first_name',
        'last_name',
        'company',
        'phone',
        'city',
        'province',
        'postal_code',
    )

    ordering = ('email',)

    fieldsets = (
        (None, {
            'fields': (
                'email',
                'password',
            )
        }),

        ('Особиста інформація', {
            'fields': (
                'first_name',
                'last_name',
                'company',
                'phone',
            )
        }),

        ('Адреса доставки', {
            'fields': (
                'address1',
                'address2',
                'city',
                'province',
                'postal_code',
            )
        }),

        ('Права доступу', {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions',
            )
        }),

        ('Важливі дати', {
            'fields': (
                'last_login',
                'date_joined',
            )
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email',
                'first_name',
                'last_name',
                'password1',
                'password2',
                'is_staff',
                'is_active',
            ),
        }),
    )

    readonly_fields = (
        'last_login',
        'date_joined',
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        if 'username' in form.base_fields:
            form.base_fields['username'].disabled = True

        return form