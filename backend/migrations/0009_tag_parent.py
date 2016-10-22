# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-10-22 11:51
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0008_visit_rating'),
    ]

    operations = [
        migrations.AddField(
            model_name='tag',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='backend.Tag'),
        ),
    ]