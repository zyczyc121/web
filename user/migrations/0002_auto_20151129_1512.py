# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('user', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Interest',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('name', models.CharField(db_index=True, max_length=30)),
                ('users', models.ManyToManyField(to=settings.AUTH_USER_MODEL, related_name='interests')),
            ],
        ),
        migrations.CreateModel(
            name='Tool',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('name', models.CharField(db_index=True, max_length=30)),
                ('users', models.ManyToManyField(to=settings.AUTH_USER_MODEL, related_name='tools')),
            ],
        ),
        migrations.AddField(
            model_name='userinfo',
            name='personal_tag',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='userinfo',
            name='twitter_account',
            field=models.CharField(blank=True, max_length=50),
        ),
    ]
