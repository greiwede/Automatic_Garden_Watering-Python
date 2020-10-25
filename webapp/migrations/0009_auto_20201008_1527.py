# Generated by Django 3.1.1 on 2020-10-08 13:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('webapp', '0008_plan_description'),
    ]

    operations = [
        migrations.AddField(
            model_name='plan',
            name='automation',
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name='Schedule',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('allow_monday', models.BooleanField(default=False)),
                ('allow_tuesday', models.BooleanField(default=False)),
                ('allow_wednesday', models.BooleanField(default=False)),
                ('allow_thursday', models.BooleanField(default=False)),
                ('allow_friday', models.BooleanField(default=False)),
                ('allow_saturday', models.BooleanField(default=False)),
                ('allow_sunday', models.BooleanField(default=False)),
                ('allow_time_start', models.TimeField(auto_now=True)),
                ('allow_time_stop', models.TimeField(auto_now=True)),
                ('deny_monday', models.BooleanField(default=False)),
                ('deny_tuesday', models.BooleanField(default=False)),
                ('deny_wednesday', models.BooleanField(default=False)),
                ('deny_thursday', models.BooleanField(default=False)),
                ('deny_friday', models.BooleanField(default=False)),
                ('deny_saturday', models.BooleanField(default=False)),
                ('deny_sunday', models.BooleanField(default=False)),
                ('deny_time_start', models.TimeField(auto_now=True)),
                ('deny_time_stop', models.TimeField(auto_now=True)),
                ('plan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='webapp.plan')),
            ],
        ),
    ]