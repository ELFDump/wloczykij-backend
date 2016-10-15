from django.contrib.auth.models import User
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet, ViewSet

from .serializers import UserSerializer


class UserViewSet(ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class CurrentUserView(ViewSet):
    permission_classes = (IsAuthenticated,)

    def list(self, request):
        return Response(UserSerializer(request.user, context={'request': request}).data)
