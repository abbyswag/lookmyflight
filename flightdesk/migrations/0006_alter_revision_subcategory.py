# Generated by Django 5.1 on 2025-01-10 19:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('flightdesk', '0005_revisioncategorysetting'),
    ]

    operations = [
        migrations.AlterField(
            model_name='revision',
            name='subcategory',
            field=models.CharField(max_length=20),
        ),
    ]
