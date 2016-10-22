import six
from django.contrib.gis.geos import Point
from django.db.models import Avg
from rest_framework import fields
from rest_framework import serializers
from django.contrib.auth.models import User

from backend.models import Place, Photo, Tag, Visit


class FixedHyperlinkedIdentityField(serializers.HyperlinkedIdentityField):
    # TODO: HyperlinkedIdentityField has some problems with utf-8 which look like a bug in Django REST Framework
    # We'll use this class as a temporary fix

    def get_name(self, obj):
        return six.text_type(str(obj), 'utf-8')


class LatLngField(fields.Field):
    def to_representation(self, value):
        return [value.y, value.x]

    def to_internal_value(self, data):
        return Point(data[1], data[0])


class TagNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag

    def to_representation(self, instance):
        return instance.name

    def to_internal_value(self, data):
        return data


class TagSerializer(serializers.HyperlinkedModelSerializer):
    url = FixedHyperlinkedIdentityField(view_name='tag-detail', lookup_field='name')
    place_count = serializers.ReadOnlyField(source='place_set.count')

    class Meta:
        model = Place
        fields = ('url', 'name', 'place_count')


class UserSerializer(serializers.HyperlinkedModelSerializer):
    first_login = fields.ReadOnlyField(source='userprofile.first_login')
    followed_tags = TagNameSerializer(source='userprofile.followed_tags', many=True)

    class Meta:
        model = User
        fields = ('url', 'username', 'first_login', 'first_name', 'last_name', 'followed_tags')

    def create(self, validated_data):
        raise NotImplementedError('No creation via JSON')

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            if attr == 'userprofile':
                continue
            setattr(instance, attr, value)

        instance.userprofile.followed_tags.clear()
        for tagname in validated_data['userprofile']['followed_tags']:
            instance.userprofile.followed_tags.add(Tag.objects.get(name=tagname))
        instance.userprofile.save()

        return instance


class PhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Photo

    def to_representation(self, instance):
        return self.context['request'].build_absolute_uri(instance.photo.resized.url)

    def to_internal_value(self, data):
        raise NotImplementedError('TODO')


class VisitSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedRelatedField(view_name='place-visit', source='place', read_only=True)

    class Meta:
        model = Visit
        fields = ('url', 'date_visited', 'rating')


class PlaceSerializer(serializers.HyperlinkedModelSerializer):
    url = FixedHyperlinkedIdentityField(view_name='place-detail')
    author = serializers.ReadOnlyField(source='author.username')
    coords = LatLngField()
    photos = PhotoSerializer(many=True, read_only=True)
    photo_upload = FixedHyperlinkedIdentityField(view_name='place-photo-upload')
    tags = TagNameSerializer(many=True)
    visit_url = FixedHyperlinkedIdentityField(view_name='place-visit')
    visit = serializers.SerializerMethodField()
    rating_avg = serializers.SerializerMethodField()
    rating_count = serializers.SerializerMethodField()
    visit_count = serializers.ReadOnlyField(source='visits.count')

    def get_visit(self, instance):
        if not self.context['request'].user.is_authenticated():
            return None

        try:
            visit = Visit.objects.get(place=instance, visitor=self.context['request'].user)
            return VisitSerializer(visit, context=self.context).data
        except Visit.DoesNotExist:
            return None

    def get_rating_avg(self, instance):
        return instance.visits.exclude(rating=0).aggregate(Avg('rating'))['rating__avg']

    def get_rating_count(self, instance):
        return instance.visits.exclude(rating=0).count()

    class Meta:
        model = Place
        fields = ('url', 'name', 'description', 'author', 'date_created', 'date_modified', 'coords', 'photos', 'photo_upload', 'tags', 'visit_url', 'visit', 'rating_avg', 'rating_count', 'visit_count')

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
