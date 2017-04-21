# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-05-04 17:44
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('course', '0004_auto_20160407_1843'),
    ]

    operations = [
        migrations.AlterField(
            model_name='course',
            name='students',
            field=models.ManyToManyField(blank=True, related_name='attend_courses', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='course',
            name='teaching_assistants',
            field=models.ManyToManyField(blank=True, related_name='ta_courses', to=settings.AUTH_USER_MODEL),
        ),
    ]