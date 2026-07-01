from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    """SAFE_METHODS - всем, для прочих методов требуется авторство."""

    def has_object_permission(self, request, view, account):
        return (request.method in permissions.SAFE_METHODS
                or account.author == request.user)
