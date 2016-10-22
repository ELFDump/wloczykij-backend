import logging

from django.contrib.auth.models import User
from rest_framework import exceptions
from rest_framework.decorators import detail_route
from rest_framework.parsers import FileUploadParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet

from backend.models import Place, Tag, Photo, Visit
from backend.permissions import IsSelfOrReadOnly
from .serializers import UserSerializer, PlaceSerializer, TagSerializer, VisitSerializer


class UserViewSet(ModelViewSet):
    """
    This endpoint lists all users registered in the system

    TODO: in the final version, the full list of users will not be accessible
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsSelfOrReadOnly,)

    def perform_update(self, serializer):
        user = serializer.save()
        user.userprofile.first_login = False
        user.userprofile.save()


class CurrentUserView(APIView):
    """
    This endpoint returns the currently logged in user.
    """

    permission_classes = (IsAuthenticated,)

    def get(self, request):
        return self.redirect(request)

    def put(self, request):
        return self.redirect(request)

    def patch(self, request):
        return self.redirect(request)

    def delete(self, request):
        return self.redirect(request)

    def redirect(self, request):
        response = Response(status=303)
        response['Location'] = reverse('user-detail', args=[request.user.pk], request=request)
        return response


class PlaceViewSet(ModelViewSet):
    # TODO: permissions
    queryset = Place.objects.all()
    serializer_class = PlaceSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @detail_route(methods=['post'], parser_classes=[FileUploadParser])
    def photo_upload(self, request, pk=None):
        photo = Photo()
        photo.photo = request.data['file']
        photo.place = self.get_object()
        photo.save()
        return Response({
            'url': request.build_absolute_uri(photo.photo.url),
            'resized_url': request.build_absolute_uri(photo.photo.resized.url)
        })

    @detail_route(methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'], serializer_class=VisitSerializer)
    def visit(self, request, pk=None):
        instance = None
        try:
            instance = Visit.objects.get(place_id=pk, visitor=request.user)
            if request.method == 'POST':
                raise exceptions.MethodNotAllowed(method=request.method)
        except Visit.DoesNotExist:
            if request.method in ['PUT', 'PATCH', 'DELETE']:
                raise exceptions.MethodNotAllowed(method=request.method)

        serializer = VisitSerializer(instance, data=request.data, partial=(request.method == 'PATCH'), context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save(place_id=pk, visitor=request.user)

        if request.method == 'DELETE':
            instance.delete()

        return Response(serializer.data)


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    lookup_field = 'name'




