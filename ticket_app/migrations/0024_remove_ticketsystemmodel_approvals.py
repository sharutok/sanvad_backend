# Generated by Django 4.2.3 on 2023-10-04 14:42

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ticket_app', '0023_alter_ticketsystemmodel_approvals'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ticketsystemmodel',
            name='approvals',
        ),
    ]
