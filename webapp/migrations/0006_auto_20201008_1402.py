# Generated by Django 3.1.1 on 2020-10-08 12:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('webapp', '0005_auto_20201008_1343'),
    ]

    operations = [
        migrations.RenameField(
            model_name='plan',
            old_name='device_status',
            new_name='name',
        ),
        migrations.RenameField(
            model_name='plan',
            old_name='plan_name',
            new_name='status',
        ),
    ]
