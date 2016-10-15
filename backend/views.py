from django.contrib.auth.models import User
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet, ViewSet

from .serializers import UserSerializer


class UserViewSet(ReadOnlyModelViewSet):
    """
    This endpoint lists all users registered in the system

    TODO: in the final version, the full list of users will not be accessible
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer


class CurrentUserView(ViewSet):
    """
    This endpoint returns the currently logged in user.
    """

    permission_classes = (IsAuthenticated,)

    def list(self, request):
        return Response(UserSerializer(request.user, context={'request': request}).data)
