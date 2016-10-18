from rest_framework import permissions


class IsSelfOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow users themselves to edit their profiles
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Don't allow deletion
        if request.method == 'DELETE':
            return False

        # Write permissions are only allowed to the user himself
        return obj.pk == request.user.pk
