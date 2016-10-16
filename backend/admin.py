from django.contrib import admin

from backend.models import Visit, Photo, Place, Tag

admin.site.register(Tag)
admin.site.register(Place)
admin.site.register(Photo)
admin.site.register(Visit)
