# Generated by Django 4.2.3 on 2023-10-10 17:58

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ticket_app', '0028_rename_string_array_field_ticketsystemmodel_approvals'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ticketsystemmodel',
            name='approvals',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.JSONField(max_length=255), default=list, size=None),
        ),
    ]
