# Generated by Django 4.2.3 on 2023-11-01 10:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('capex_app', '0032_capex1_capex_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='capex1',
            name='flow_type',
            field=models.CharField(max_length=50, null=True),
        ),
    ]
