# Generated by Django 4.2.6 on 2023-12-22 08:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('flightdesk', '0003_alter_booking_confirmation_arl_alter_booking_gds_pnr'),
    ]

    operations = [
        migrations.AlterField(
            model_name='booking',
            name='amount',
            field=models.DecimalField(decimal_places=2, max_digits=10, null=True),
        ),
    ]