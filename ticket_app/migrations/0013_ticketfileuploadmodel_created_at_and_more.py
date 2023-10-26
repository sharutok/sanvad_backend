# Generated by Django 4.2.3 on 2023-10-02 14:24

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('ticket_app', '0012_ticketfileuploadmodel_delete_flag_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='ticketfileuploadmodel',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='ticketfileuploadmodel',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
