# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-04-12 02:00
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('competition', '0028_auto_20170312_0900'),
    ]

    operations = [
        migrations.AddField(
            model_name='competition',
            name='evaluate_reverse',
            field=models.BooleanField(default=False),
        ),
    ]