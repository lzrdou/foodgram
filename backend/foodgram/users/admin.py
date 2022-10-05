from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Follow, User


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
    search_fields = ('email', 'username')
    list_filter = ('email', 'username')


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    """Модель администратора подписок."""
    list_display = (
        'user',
        'author'
    )
    search_fields = ('user', 'author')
    list_filter = ('user', 'author')
