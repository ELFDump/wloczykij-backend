import os
import time
from django.db import models
from django.contrib.gis.db import models as gis_models
from django.utils.encoding import force_bytes


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return force_bytes('#'+self.name)


class Place(models.Model):
    name = models.CharField(max_length=300)
    tags = models.ManyToManyField(Tag)
    author = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, related_name='added_places')
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    coords = gis_models.PointField()

    def __str__(self):
        return force_bytes(self.name + ' @ ' + str(self.coords.x) + ';' + str(self.coords.y))


def photo_path(instance, filename):
    return 'photos/{0}/{1}{2}'.format(instance.place.id, int(round(time.time() * 1000)), os.path.splitext(filename)[1])


class Photo(models.Model):
    photo = models.ImageField(upload_to=photo_path)
    place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name='photos')

    def __str__(self):
        return force_bytes('Photo for ' + str(self.place))


class Visit(models.Model):
    place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name='visits')
    visitor = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='visited_places')
    date_visited = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return force_bytes(str(self.visitor) + '\'s visit to ' + str(self.place) + ' at ' + str(self.date_visited))
