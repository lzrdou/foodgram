from rest_framework import permissions


class AdminPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user.is_authenticated
            and (request.user.is_staff or request.user.is_admin)
        )


class RecipeAuthorOrAdminPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return bool(
            request.method in permissions.SAFE_METHODS
            or obj.author == request.user
            or request.user.is_admin
        )


class AddedUserPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return bool(
            obj.user == request.user
        )
