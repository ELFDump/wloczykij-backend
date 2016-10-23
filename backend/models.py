import logging
import os
import time

import stdimage
from PIL import Image
from django.contrib.auth.models import User
from django.contrib.gis.db import models as gis_models
from django.core.files.base import ContentFile
from django.db import models
from django.db.models.signals import post_save
from django.utils.encoding import force_bytes
from six import BytesIO
from stdimage.utils import render_variations


class UserProfile(models.Model):
    user = models.OneToOneField(User)
    first_login = models.BooleanField(default=True)
    followed_tags = models.ManyToManyField('Tag', blank=True, related_name='followers')

    def __str__(self):
        return force_bytes("%s's profile" % self.user)


def create_user_profile(sender, instance, created, **kwargs):
    if created:
       profile, created = UserProfile.objects.get_or_create(user=instance)

post_save.connect(create_user_profile, sender=User)


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, related_name='children')

    def __str__(self):
        return force_bytes('#'+self.name)


class Place(models.Model):
    name = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    tags = models.ManyToManyField(Tag)
    author = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, related_name='added_places')
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    coords = gis_models.PointField()

    def __str__(self):
        return force_bytes(self.name + ' @ ' + str(self.coords.x) + ';' + str(self.coords.y))


def photo_path(instance, filename):
    return 'photos/{0}/{1}{2}'.format(instance.place.id, int(round(time.time() * 1000)), os.path.splitext(filename)[1])


# see https://github.com/codingjoe/django-stdimage/issues/66#issuecomment-180309788
def photo_render_variations(file_name, variations, storage):
    with storage.open(file_name) as f:
        with Image.open(f) as image:
            file_format = image.format
            logging.info('File format: ' + file_format)
            if file_format == 'JPEG':
                exif = image._getexif()

                # if image has exif data about orientation, let's rotate it
                orientation_key = 274  # cf ExifTags
                if exif and orientation_key in exif:
                    orientation = exif[orientation_key]

                    rotate_values = {
                        3: Image.ROTATE_180,
                        6: Image.ROTATE_270,
                        8: Image.ROTATE_90
                    }

                    if orientation in rotate_values:
                        image = image.transpose(rotate_values[orientation])

                    file_buffer = BytesIO()
                    image.save(file_buffer, file_format)
                    f = ContentFile(file_buffer.getvalue())
                    storage.delete(file_name)
                    storage.save(file_name, f)

    # render stdimage variations
    render_variations(file_name, variations, replace=True, storage=storage)

    return False  # prevent default rendering


class Photo(models.Model):
    photo = stdimage.StdImageField(upload_to=photo_path, render_variations=photo_render_variations, variations={'resized': {'width': 2048, 'height': 2048}})
    place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name='photos')

    def __str__(self):
        return force_bytes('Photo for ' + str(self.place))


RATINGS = (
    (0, '---'),
    (1, '*'),
    (2, '**'),
    (3, '***'),
    (4, '****'),
)


class Visit(models.Model):
    place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name='visits')
    visitor = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='visited_places')
    date_visited = models.DateTimeField(auto_now_add=True)
    rating = models.IntegerField(default=0, blank=True, choices=RATINGS)

    class Meta:
        unique_together = ['place', 'visitor']

    def __str__(self):
        return force_bytes(str(self.visitor) + '\'s visit to ' + str(self.place) + ' at ' + str(self.date_visited))
