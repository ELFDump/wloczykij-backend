# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-10-19 20:13
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0003_auto_20161019_1908'),
    ]

    operations = [
        migrations.AddField(
            model_name='place',
            name='description',
            field=models.TextField(blank=True),
        ),
    ]
