# Generated by Django 3.1 on 2020-10-25 14:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('webapp', '0026_auto_20201025_1450'),
    ]

    operations = [
        migrations.RenameField(
            model_name='wateringstatistic',
            old_name='duration',
            new_name='duration_seconds',
        ),
    ]