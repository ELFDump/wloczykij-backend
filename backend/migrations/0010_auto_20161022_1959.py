# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-10-22 19:59
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0009_tag_parent'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='followed_tags',
            field=models.ManyToManyField(blank=True, related_name='followers', to='backend.Tag'),
        ),
    ]
