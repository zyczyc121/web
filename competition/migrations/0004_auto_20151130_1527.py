# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('competition', '0003_auto_20151130_1441'),
    ]

    operations = [
        migrations.AlterField(
            model_name='data',
            name='size',
            field=models.BigIntegerField(),
        ),
    ]
