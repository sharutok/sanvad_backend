# Generated by Django 4.2.3 on 2023-07-29 11:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('capex_app', '0004_remove_capex1_site_delivery_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='capex1',
            name='site_delivery_date',
            field=models.DateField(null=True),
        ),
    ]
