# Generated by Django 5.1 on 2024-12-23 16:15

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('flightdesk', '0002_airline_booking_remark_calllog_airline'),
    ]

    operations = [
        migrations.CreateModel(
            name='Revision',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subcategory', models.CharField(choices=[('cancelled', 'Cancelled'), ('refund', 'Refund')], max_length=20)),
                ('note', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('booking', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='flightdesk.booking')),
            ],
        ),
    ]
