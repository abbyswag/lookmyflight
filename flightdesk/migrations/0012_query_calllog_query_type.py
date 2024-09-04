# Generated by Django 5.1 on 2024-09-04 00:23

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('flightdesk', '0011_remove_email_added_by_email_booking'),
    ]

    operations = [
        migrations.CreateModel(
            name='Query',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=50, unique=True)),
            ],
        ),
        migrations.AddField(
            model_name='calllog',
            name='query_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='flightdesk.query'),
        ),
    ]