# Generated by Django 5.1 on 2024-10-01 03:57

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('flightdesk', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='calllog',
            old_name='airline',
            new_name='airline_id',
        ),
    ]