# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='FacebookLike',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('user_id', models.IntegerField()),
                ('facebook_id', models.BigIntegerField()),
                ('name', models.TextField(null=True, blank=True)),
                ('category', models.TextField(null=True, blank=True)),
                ('created_time', models.DateTimeField(null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='FacebookProfile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('about_me', models.TextField(null=True, blank=True)),
                ('facebook_id', models.BigIntegerField(unique=True, null=True, blank=True)),
                ('access_token', models.TextField(help_text='Facebook token for offline access', null=True, blank=True)),
                ('facebook_name', models.CharField(max_length=255, null=True, blank=True)),
                ('facebook_profile_url', models.TextField(null=True, blank=True)),
                ('website_url', models.TextField(null=True, blank=True)),
                ('blog_url', models.TextField(null=True, blank=True)),
                ('date_of_birth', models.DateField(null=True, blank=True)),
                ('gender', models.CharField(blank=True, max_length=1, null=True, choices=[('m', 'Male'), ('f', 'Female')])),
                ('raw_data', models.TextField(null=True, blank=True)),
                ('facebook_open_graph', models.NullBooleanField(help_text='Determines if this user want to share via open graph')),
                ('new_token_required', models.BooleanField(default=False, help_text='Set to true if the access token is outdated or lacks permissions')),
                ('image', models.ImageField(max_length=255, null=True, upload_to='images/facebook_profiles/%Y/%m/%d', blank=True)),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='FacebookUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('user_id', models.IntegerField()),
                ('facebook_id', models.BigIntegerField()),
                ('name', models.TextField(null=True, blank=True)),
                ('gender', models.CharField(blank=True, max_length=1, null=True, choices=[('F', 'female'), ('M', 'male')])),
            ],
        ),
        migrations.CreateModel(
            name='OpenGraphShare',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('action_domain', models.CharField(max_length=255)),
                ('facebook_user_id', models.BigIntegerField()),
                ('share_dict', models.TextField(null=True, blank=True)),
                ('object_id', models.PositiveIntegerField(null=True, blank=True)),
                ('error_message', models.TextField(null=True, blank=True)),
                ('last_attempt', models.DateTimeField(auto_now_add=True, null=True)),
                ('retry_count', models.IntegerField(null=True, blank=True)),
                ('share_id', models.CharField(max_length=255, null=True, blank=True)),
                ('completed_at', models.DateTimeField(null=True, blank=True)),
                ('removed_at', models.DateTimeField(null=True, blank=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('content_type', models.ForeignKey(blank=True, to='contenttypes.ContentType', null=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': None,
            },
        ),
        migrations.AlterUniqueTogether(
            name='facebookuser',
            unique_together=set([('user_id', 'facebook_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='facebooklike',
            unique_together=set([('user_id', 'facebook_id')]),
        ),
    ]
