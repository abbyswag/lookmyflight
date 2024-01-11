# Generated by Django 5.0.1 on 2024-01-11 09:27

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('flightdesk', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='calllog',
            name='email',
            field=models.EmailField(blank=True, max_length=254),
        ),
        migrations.AlterField(
            model_name='mybooking',
            name='mco',
            field=models.CharField(choices=[('waiting', 'Waiting'), ('cleared', 'Cleared'), ('Failed', 'failed'), ('refunded', 'Refunded')], default='initiated', max_length=20),
        ),
        migrations.CreateModel(
            name='EmailAttachtment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('attachment', models.ImageField(blank=True, upload_to='', verbose_name='/email_attachments/')),
                ('email', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='flightdesk.email')),
            ],
        ),
    ]