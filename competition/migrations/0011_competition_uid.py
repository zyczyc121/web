# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-07-29 12:13
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('competition', '0010_auto_20160617_1602'),
    ]

    operations = [
        migrations.AddField(
            model_name='competition',
            name='uid',
            field=models.CharField(db_index=True, max_length=50, null=True, unique=True),
        ),
    ]
