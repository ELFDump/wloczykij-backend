import logging

from rest_framework import permissions


class IsSelfOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow users themselves to edit their profiles
    """

    def has_permission(self, request, view):
        if view.action == 'create':
            return False

        return True

    def has_object_permission(self, request, view, obj):
        logging.info(request.method)

        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Don't allow deletion
        if request.method == 'DELETE':
            return False

        # Write permissions are only allowed to the user himself
        return obj == request.user
