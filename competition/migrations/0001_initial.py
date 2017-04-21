# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import competition.models
import django.core.files.storage
import ckeditor_uploader.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=30)),
            ],
        ),
        migrations.CreateModel(
            name='Competition',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('description', models.TextField()),
                ('category', models.IntegerField(choices=[(1, 'Championship'), (2, 'Knowledge')])),
                ('award', models.CharField(max_length=10)),
                ('start_datetime', models.DateTimeField()),
                ('end_datetime', models.DateTimeField()),
                ('submit_per_day', models.IntegerField(default=5)),
                ('final_submit_count', models.IntegerField(default=2)),
                ('evaluation', models.CharField(max_length=10)),
                ('num_line', models.IntegerField()),
                ('public_ratio', models.IntegerField()),
                ('public_truth', models.FileField(upload_to=competition.models.truth_file_name, storage=django.core.files.storage.FileSystemStorage('/var/www/dc/truth/'))),
                ('private_truth', models.FileField(upload_to=competition.models.truth_file_name, storage=django.core.files.storage.FileSystemStorage('/var/www/dc/truth/'))),
                ('introduction', ckeditor_uploader.fields.RichTextUploadingField()),
                ('rules', ckeditor_uploader.fields.RichTextUploadingField()),
                ('data_description', ckeditor_uploader.fields.RichTextUploadingField()),
                ('logo', models.ImageField(upload_to=competition.models.resource_file_name)),
                ('banner', models.ImageField(upload_to=competition.models.resource_file_name)),
                ('host', models.ForeignKey(related_name='host_competitions', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Data',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('content', models.FileField(storage=django.core.files.storage.FileSystemStorage('/var/www/dc/data/'), blank=True, null=True, upload_to=competition.models.resource_file_name)),
                ('baidu_url', models.URLField(blank=True)),
                ('baidu_code', models.CharField(blank=True, max_length=5)),
                ('dropbox_url', models.URLField(blank=True)),
                ('name', models.CharField(max_length=20)),
                ('size', models.IntegerField()),
                ('filetype', models.CharField(max_length=10)),
                ('competition', models.ForeignKey(related_name='data', to='competition.Competition')),
            ],
        ),
        migrations.CreateModel(
            name='Detail',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('title', models.CharField(unique=True, max_length=50)),
                ('content', ckeditor_uploader.fields.RichTextUploadingField()),
                ('slug', models.SlugField()),
                ('order', models.IntegerField()),
                ('competition', models.ForeignKey(to='competition.Competition')),
            ],
        ),
        migrations.CreateModel(
            name='Leaderboard',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('num_submission', models.IntegerField()),
                ('score', models.FloatField()),
                ('submission_datetime', models.DateTimeField()),
            ],
        ),
        migrations.CreateModel(
            name='Participation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('join_datetime', models.DateTimeField()),
                ('competition', models.ForeignKey(to='competition.Competition')),
            ],
        ),
        migrations.CreateModel(
            name='Submission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('content', models.FileField(upload_to=competition.models.resource_file_name, storage=django.core.files.storage.FileSystemStorage('/var/www/dc/submission/'))),
                ('description', models.CharField(max_length=100)),
                ('display_name', models.CharField(max_length=255)),
                ('submit_datetime', models.DateTimeField()),
                ('message', models.CharField(blank=True, max_length=50)),
                ('final_submit', models.BooleanField(default=False)),
                ('public_score', models.FloatField()),
                ('private_score', models.FloatField()),
                ('remote_addr', models.GenericIPAddressField(blank=True, null=True)),
                ('status', models.IntegerField(choices=[(1, 'pending'), (2, 'success'), (3, 'error')])),
                ('competition', models.ForeignKey(related_name='submissions', to='competition.Competition')),
            ],
        ),
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=20)),
                ('create_datetime', models.DateTimeField()),
                ('competition', models.ForeignKey(related_name='teams', to='competition.Competition')),
                ('leader', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('members', models.ManyToManyField(through='competition.Participation', related_name='teams', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Timeline',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('mark_datetime', models.DateTimeField()),
                ('competition', models.ForeignKey(to='competition.Competition')),
            ],
        ),
        migrations.AddField(
            model_name='submission',
            name='team',
            field=models.ForeignKey(related_name='submissions', to='competition.Team'),
        ),
        migrations.AddField(
            model_name='submission',
            name='user',
            field=models.ForeignKey(related_name='submissions', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='participation',
            name='team',
            field=models.ForeignKey(null=True, blank=True, to='competition.Team'),
        ),
        migrations.AddField(
            model_name='participation',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='leaderboard',
            name='team',
            field=models.ForeignKey(to='competition.Team'),
        ),
        migrations.AddField(
            model_name='competition',
            name='participants',
            field=models.ManyToManyField(through='competition.Participation', related_name='participate_competitions', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='participation',
            unique_together=set([('competition', 'user')]),
        ),
        migrations.AlterUniqueTogether(
            name='data',
            unique_together=set([('competition', 'name')]),
        ),
    ]
