from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class UserAdmin(UserAdmin):
    """Модель администратора пользователей."""
    list_display = (
        'id',
        'username',
        'email',
        'password',
        'last_name',
        'first_name',
        'role'
    )
    search_fields = ('username',)
    list_filter = ('email', 'username')
