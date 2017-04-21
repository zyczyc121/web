# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('competition', '0004_auto_20151130_1527'),
    ]

    operations = [
        migrations.AddField(
            model_name='competition',
            name='sponsor',
            field=models.CharField(max_length=50, blank=True),
        ),
    ]
