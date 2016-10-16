import six
from django.contrib.gis.geos import Point
from rest_framework import fields
from rest_framework import relations
from rest_framework import serializers
from django.contrib.auth.models import User

from backend.models import Place, Photo


class FixedHyperlinkedIdentityField(serializers.HyperlinkedIdentityField):
    # TODO: HyperlinkedIdentityField has some problems with utf-8 which look like a bug in Django REST Framework
    # We'll use this class as a temporary fix

    def get_name(self, obj):
        return six.text_type(str(obj), 'utf-8')


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'username', 'first_name', 'last_name')


class LatLngField(fields.Field):
    def to_representation(self, value):
        return [value.x, value.y]

    def to_internal_value(self, data):
        return Point(data[0], data[1])


class PhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Photo

    def to_representation(self, instance):
        return self.context['request'].build_absolute_uri(instance.photo.url)

    def to_internal_value(self, data):
        raise NotImplementedError('TODO')


class PlaceSerializer(serializers.HyperlinkedModelSerializer):
    url = FixedHyperlinkedIdentityField(view_name='place-detail')
    author = serializers.ReadOnlyField(source='author.username')
    coords = LatLngField()
    photos = PhotoSerializer(many=True)

    class Meta:
        model = Place
        fields = ('url', 'name', 'author', 'date_created', 'date_modified', 'coords', 'photos')

