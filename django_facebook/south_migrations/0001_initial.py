# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models
from django.conf import settings

'''
Support for Django custom user models
See this blog post for inspiration

http://kevindias.com/writing/django-custom-user-models-south-and-reusable-apps/
https://github.com/stephenmcd/mezzanine/blob/master/mezzanine/core/migrations/0005_auto__chg_field_sitepermission_user__del_unique_sitepermission_user.py
'''
from django_facebook.utils import get_migration_data
User, user_model_label, user_orm_label = get_migration_data()


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'FacebookUser'
        db.create_table(u'django_facebook_facebookuser', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user_id', self.gf('django.db.models.fields.IntegerField')()),
            ('facebook_id', self.gf('django.db.models.fields.BigIntegerField')()),
            ('name', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('gender', self.gf('django.db.models.fields.CharField')(max_length=1, null=True, blank=True)),
        ))
        db.send_create_signal(u'django_facebook', ['FacebookUser'])

        # Adding unique constraint on 'FacebookUser', fields ['user_id', 'facebook_id']
        db.create_unique(u'django_facebook_facebookuser', ['user_id', 'facebook_id'])

        # Adding model 'FacebookLike'
        db.create_table(u'django_facebook_facebooklike', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user_id', self.gf('django.db.models.fields.IntegerField')()),
            ('facebook_id', self.gf('django.db.models.fields.BigIntegerField')()),
            ('name', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('category', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('created_time', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'django_facebook', ['FacebookLike'])

        # Adding unique constraint on 'FacebookLike', fields ['user_id', 'facebook_id']
        db.create_unique(u'django_facebook_facebooklike', ['user_id', 'facebook_id'])

        # Adding model 'FacebookProfile'
        db.create_table(u'django_facebook_facebookprofile', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('about_me', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('facebook_id', self.gf('django.db.models.fields.BigIntegerField')(unique=True, null=True, blank=True)),
            ('access_token', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('facebook_name', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('facebook_profile_url', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('website_url', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('blog_url', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('date_of_birth', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('gender', self.gf('django.db.models.fields.CharField')(max_length=1, null=True, blank=True)),
            ('raw_data', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('facebook_open_graph', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('new_token_required', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('image', self.gf('django.db.models.fields.files.ImageField')(max_length=255, null=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.OneToOneField')(to=orm[user_orm_label], unique=True)),
        ))
        db.send_create_signal(u'django_facebook', ['FacebookProfile'])

        if getattr(settings, 'AUTH_USER_MODEL', None) == 'django_facebook.FacebookCustomUser':
            # Adding model 'FacebookCustomUser'
            db.create_table(u'django_facebook_facebookcustomuser', (
                (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
                ('password', self.gf('django.db.models.fields.CharField')(max_length=128)),
                ('last_login', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
                ('is_superuser', self.gf('django.db.models.fields.BooleanField')(default=False)),
                ('username', self.gf('django.db.models.fields.CharField')(unique=True, max_length=30)),
                ('first_name', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
                ('last_name', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
                ('email', self.gf('django.db.models.fields.EmailField')(max_length=75, blank=True)),
                ('is_staff', self.gf('django.db.models.fields.BooleanField')(default=False)),
                ('is_active', self.gf('django.db.models.fields.BooleanField')(default=True)),
                ('date_joined', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
                ('about_me', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
                ('facebook_id', self.gf('django.db.models.fields.BigIntegerField')(unique=True, null=True, blank=True)),
                ('access_token', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
                ('facebook_name', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
                ('facebook_profile_url', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
                ('website_url', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
                ('blog_url', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
                ('date_of_birth', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
                ('gender', self.gf('django.db.models.fields.CharField')(max_length=1, null=True, blank=True)),
                ('raw_data', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
                ('facebook_open_graph', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
                ('new_token_required', self.gf('django.db.models.fields.BooleanField')(default=False)),
                ('image', self.gf('django.db.models.fields.files.ImageField')(max_length=255, null=True, blank=True)),
                ('state', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ))
            db.send_create_signal(u'django_facebook', ['FacebookCustomUser'])

            # Adding M2M table for field groups on 'FacebookCustomUser'
            m2m_table_name = db.shorten_name(u'django_facebook_facebookcustomuser_groups')
            db.create_table(m2m_table_name, (
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
                ('facebookcustomuser', models.ForeignKey(orm[u'django_facebook.facebookcustomuser'], null=False)),
                ('group', models.ForeignKey(orm[u'auth.group'], null=False))
            ))
            db.create_unique(m2m_table_name, ['facebookcustomuser_id', 'group_id'])

            # Adding M2M table for field user_permissions on 'FacebookCustomUser'
            m2m_table_name = db.shorten_name(u'django_facebook_facebookcustomuser_user_permissions')
            db.create_table(m2m_table_name, (
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
                ('facebookcustomuser', models.ForeignKey(orm[u'django_facebook.facebookcustomuser'], null=False)),
                ('permission', models.ForeignKey(orm[u'auth.permission'], null=False))
            ))
            db.create_unique(m2m_table_name, ['facebookcustomuser_id', 'permission_id'])

        # Adding model 'OpenGraphShare'
        db.create_table('django_facebook_open_graph_share', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm[user_orm_label])),
            ('action_domain', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('facebook_user_id', self.gf('django.db.models.fields.BigIntegerField')()),
            ('share_dict', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'], null=True, blank=True)),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('error_message', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('last_attempt', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True)),
            ('retry_count', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('share_id', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
            ('completed_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('removed_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, db_index=True, blank=True)),
        ))
        db.send_create_signal(u'django_facebook', ['OpenGraphShare'])


    def backwards(self, orm):
        # Removing unique constraint on 'FacebookLike', fields ['user_id', 'facebook_id']
        db.delete_unique(u'django_facebook_facebooklike', ['user_id', 'facebook_id'])

        # Removing unique constraint on 'FacebookUser', fields ['user_id', 'facebook_id']
        db.delete_unique(u'django_facebook_facebookuser', ['user_id', 'facebook_id'])

        # Deleting model 'FacebookUser'
        db.delete_table(u'django_facebook_facebookuser')

        # Deleting model 'FacebookLike'
        db.delete_table(u'django_facebook_facebooklike')

        # Deleting model 'FacebookProfile'
        db.delete_table(u'django_facebook_facebookprofile')

        # Deleting model 'FacebookCustomUser'
        db.delete_table(u'django_facebook_facebookcustomuser')

        # Removing M2M table for field groups on 'FacebookCustomUser'
        db.delete_table(db.shorten_name(u'django_facebook_facebookcustomuser_groups'))

        # Removing M2M table for field user_permissions on 'FacebookCustomUser'
        db.delete_table(db.shorten_name(u'django_facebook_facebookcustomuser_user_permissions'))

        # Deleting model 'OpenGraphShare'
        db.delete_table('django_facebook_open_graph_share')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        user_model_label: {
            'Meta': {'object_name': User.__name__, 'db_table': "'%s'" % User._meta.db_table},
            'about_me': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'access_token': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'blog_url': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'date_of_birth': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'facebook_id': ('django.db.models.fields.BigIntegerField', [], {'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'facebook_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'facebook_open_graph': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'facebook_profile_url': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'new_token_required': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'raw_data': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'}),
            'website_url': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'})
        },
        u'django_facebook.facebooklike': {
            'Meta': {'unique_together': "(['user_id', 'facebook_id'],)", 'object_name': 'FacebookLike'},
            'category': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'created_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'facebook_id': ('django.db.models.fields.BigIntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'user_id': ('django.db.models.fields.IntegerField', [], {})
        },
        u'django_facebook.facebookprofile': {
            'Meta': {'object_name': 'FacebookProfile'},
            'about_me': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'access_token': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'blog_url': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'date_of_birth': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'facebook_id': ('django.db.models.fields.BigIntegerField', [], {'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'facebook_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'facebook_open_graph': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'facebook_profile_url': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'new_token_required': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'raw_data': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['%s']" % user_orm_label, 'unique': 'True'}),
            'website_url': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'})
        },
        u'django_facebook.facebookuser': {
            'Meta': {'unique_together': "(['user_id', 'facebook_id'],)", 'object_name': 'FacebookUser'},
            'facebook_id': ('django.db.models.fields.BigIntegerField', [], {}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'user_id': ('django.db.models.fields.IntegerField', [], {})
        },
        u'django_facebook.opengraphshare': {
            'Meta': {'object_name': 'OpenGraphShare', 'db_table': "'django_facebook_open_graph_share'"},
            'action_domain': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'completed_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'error_message': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'facebook_user_id': ('django.db.models.fields.BigIntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_attempt': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'removed_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'retry_count': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'share_dict': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'share_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['%s']" % user_orm_label})
        }
    }

    complete_apps = ['django_facebook']
