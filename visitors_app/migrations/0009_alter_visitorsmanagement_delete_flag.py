# Generated by Django 4.2.3 on 2023-11-07 10:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('visitors_app', '0008_visitorsmanagement_raised_by'),
    ]

    operations = [
        migrations.AlterField(
            model_name='visitorsmanagement',
            name='delete_flag',
            field=models.BooleanField(default=False),
        ),
    ]
