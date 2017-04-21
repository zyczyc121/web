# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-09-30 04:16
from __future__ import unicode_literals

import ckeditor_uploader.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('competition', '0018_auto_20160929_0429'),
    ]

    operations = [
        migrations.AddField(
            model_name='competition',
            name='ShowWinner_datetime',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='competition',
            name='winners',
            field=ckeditor_uploader.fields.RichTextUploadingField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='competition',
            name='winners_en',
            field=ckeditor_uploader.fields.RichTextUploadingField(blank=True, null=True),
        ),
    ]
