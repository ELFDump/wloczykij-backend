import six
from django.contrib.gis.geos import Point
from rest_framework import fields
from rest_framework import serializers
from django.contrib.auth.models import User

from backend.models import Place, Photo, Tag


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
        return [value.y, value.x]

    def to_internal_value(self, data):
        return Point(data[1], data[0])


class PhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Photo

    def to_representation(self, instance):
        return self.context['request'].build_absolute_uri(instance.photo.resized.url)

    def to_internal_value(self, data):
        raise NotImplementedError('TODO')


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag

    def to_representation(self, instance):
        return instance.name

    def to_internal_value(self, data):
        return data


class PlaceSerializer(serializers.HyperlinkedModelSerializer):
    url = FixedHyperlinkedIdentityField(view_name='place-detail')
    author = serializers.ReadOnlyField(source='author.username')
    coords = LatLngField()
    photos = PhotoSerializer(many=True, read_only=True)
    photo_upload = FixedHyperlinkedIdentityField(view_name='place-photo-upload')
    tags = TagSerializer(many=True)

    class Meta:
        model = Place
        fields = ('url', 'name', 'author', 'date_created', 'date_modified', 'coords', 'photos', 'photo_upload', 'tags')

    def create(self, validated_data):
        tags = validated_data['tags']
        del validated_data['tags']

        instance = Place.objects.create(**validated_data)

        for tagname in tags:
            instance.tags.add(Tag.objects.get(name=tagname))

        instance.save()
        return instance

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            if attr == 'tags':
                continue
            setattr(instance, attr, value)

        instance.tags.clear()
        for tagname in validated_data['tags']:
            instance.tags.add(Tag.objects.get(name=tagname))
        instance.save()

        return instance
