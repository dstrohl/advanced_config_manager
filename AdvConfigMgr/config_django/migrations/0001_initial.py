# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ConfigOptions',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128, unique=True)),
                ('value', models.TextField()),
                ('default_value', models.TextField(blank=True, null=True)),
                ('description', models.CharField(max_length=256, blank=True, null=True)),
                ('verbose_name', models.CharField(max_length=128, blank=True, null=True)),
                ('datatype', models.CharField(max_length=32)),
                ('hidden', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name_plural': 'Manage Configuration Options',
                'verbose_name': 'Configuration Option',
            },
        ),
        migrations.CreateModel(
            name='ConfigSections',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128, unique=True)),
                ('description', models.CharField(max_length=256, blank=True, null=True)),
                ('verbose_name', models.CharField(max_length=128, blank=True, null=True)),
                ('hidden', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name_plural': 'Manage Configuration Sections',
                'verbose_name': 'Configuration Section',
            },
        ),
        migrations.AddField(
            model_name='configoptions',
            name='section',
            field=models.ForeignKey(related_name='options', to='config_django.ConfigSections'),
        ),
    ]
