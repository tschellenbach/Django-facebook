# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'FacebookUser'
        db.create_table('django_facebook_facebookuser', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user_id', self.gf('django.db.models.fields.IntegerField')()),
            ('facebook_id', self.gf('django.db.models.fields.BigIntegerField')()),
            ('name', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal('django_facebook', ['FacebookUser'])

        # Adding unique constraint on 'FacebookUser', fields ['user_id', 'facebook_id']
        db.create_unique('django_facebook_facebookuser', ['user_id', 'facebook_id'])

        # Adding model 'FacebookLike'
        db.create_table('django_facebook_facebooklike', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user_id', self.gf('django.db.models.fields.IntegerField')()),
            ('facebook_id', self.gf('django.db.models.fields.BigIntegerField')()),
            ('name', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('category', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('created_time', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal('django_facebook', ['FacebookLike'])

        # Adding unique constraint on 'FacebookLike', fields ['user_id', 'facebook_id']
        db.create_unique('django_facebook_facebooklike', ['user_id', 'facebook_id'])


    def backwards(self, orm):
        
        # Deleting model 'FacebookUser'
        db.delete_table('django_facebook_facebookuser')

        # Removing unique constraint on 'FacebookUser', fields ['user_id', 'facebook_id']
        db.delete_unique('django_facebook_facebookuser', ['user_id', 'facebook_id'])

        # Deleting model 'FacebookLike'
        db.delete_table('django_facebook_facebooklike')

        # Removing unique constraint on 'FacebookLike', fields ['user_id', 'facebook_id']
        db.delete_unique('django_facebook_facebooklike', ['user_id', 'facebook_id'])


    models = {
        'django_facebook.facebooklike': {
            'Meta': {'unique_together': "(['user_id', 'facebook_id'],)", 'object_name': 'FacebookLike'},
            'category': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'created_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'facebook_id': ('django.db.models.fields.BigIntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'user_id': ('django.db.models.fields.IntegerField', [], {})
        },
        'django_facebook.facebookuser': {
            'Meta': {'unique_together': "(['user_id', 'facebook_id'],)", 'object_name': 'FacebookUser'},
            'facebook_id': ('django.db.models.fields.BigIntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'user_id': ('django.db.models.fields.IntegerField', [], {})
        }
    }

    complete_apps = ['django_facebook']
