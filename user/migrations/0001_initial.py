# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Skill',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('label', models.CharField(db_index=True, max_length=20)),
                ('category', models.IntegerField(db_index=True)),
                ('users', models.ManyToManyField(related_name='skills', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='UserInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('display_name', models.CharField(max_length=30)),
                ('receive_update', models.BooleanField()),
                ('avatar', models.ImageField(blank=True, upload_to='image/avatar')),
                ('bio', models.TextField(blank=True, max_length=500)),
                ('occupation', models.CharField(blank=True, max_length=50)),
                ('birth_date', models.DateField(null=True, blank=True)),
                ('province', models.CharField(blank=True, max_length=50)),
                ('city', models.CharField(blank=True, max_length=50)),
                ('country', models.CharField(blank=True, max_length=50)),
                ('website_url', models.CharField(blank=True, max_length=255)),
                ('github_account', models.CharField(blank=True, max_length=50)),
                ('linkedin_url', models.CharField(blank=True, max_length=255)),
                ('status', models.IntegerField(choices=[(1, 'pending'), (2, 'active'), (3, 'forbidden')])),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL, related_name='info')),
            ],
        ),
        migrations.CreateModel(
            name='UserModification',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('key', models.CharField(max_length=128)),
                ('action', models.IntegerField(choices=[(1, 'activation'), (2, 'reset password')])),
                ('expire_datetime', models.DateTimeField()),
                ('arg1', models.IntegerField(null=True, blank=True)),
                ('arg2', models.IntegerField(null=True, blank=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AlterIndexTogether(
            name='usermodification',
            index_together=set([('user', 'action')]),
        ),
    ]
