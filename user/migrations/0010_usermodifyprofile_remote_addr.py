# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-08-30 10:59
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0009_auto_20160830_1055'),
    ]

    operations = [
        migrations.AddField(
            model_name='usermodifyprofile',
            name='remote_addr',
            field=models.GenericIPAddressField(blank=True, null=True),
        ),
    ]
