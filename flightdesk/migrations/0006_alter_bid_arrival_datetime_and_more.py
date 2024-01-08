# Generated by Django 5.0.1 on 2024-01-08 14:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('flightdesk', '0005_alter_bid_mco'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bid',
            name='arrival_datetime',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='bid',
            name='departure_datetime',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='bid',
            name='flight_number',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='bid',
            name='from_location',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='bid',
            name='mco',
            field=models.CharField(choices=[('Waiting', 'waiting'), ('Cleared', 'cleared'), ('Failed', 'failed'), ('Refunded', 'refunded')], default='initiated', max_length=20),
        ),
        migrations.AlterField(
            model_name='bid',
            name='to_location',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
