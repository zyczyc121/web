# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('competition', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='detail',
            name='title',
            field=models.CharField(max_length=50),
        ),
        migrations.AlterUniqueTogether(
            name='detail',
            unique_together=set([('competition', 'slug')]),
        ),
    ]
