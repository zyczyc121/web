# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-09-18 08:00
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('competition', '0015_auto_20160808_0756'),
    ]

    operations = [
        migrations.AddField(
            model_name='competition',
            name='finalCaculate_datetime',
            field=models.DateTimeField(null=True),
        ),
    ]
