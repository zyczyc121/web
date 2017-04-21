# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('competition', '0002_auto_20151130_0840'),
    ]

    operations = [
        migrations.AddField(
            model_name='competition',
            name='allow_overdue_submission',
            field=models.BooleanField(default=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='data',
            name='name',
            field=models.CharField(max_length=50),
        ),
    ]
