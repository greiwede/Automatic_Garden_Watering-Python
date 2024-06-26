# Generated by Django 3.1 on 2020-10-22 12:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webapp', '0017_plan_is_active_plan'),
    ]

    operations = [
        migrations.AddField(
            model_name='weatherstatus',
            name='description',
            field=models.CharField(default=1, max_length=128),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='weatherstatus',
            name='icon',
            field=models.CharField(default=1, max_length=3),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='weatherstatus',
            name='name',
            field=models.CharField(default=1, max_length=32),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='weatherstatus',
            name='owm_id',
            field=models.IntegerField(default=1),
            preserve_default=False,
        ),
    ]
