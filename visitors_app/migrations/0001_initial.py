# Generated by Django 4.2.3 on 2023-08-17 17:01

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='VisitorsManagement',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('appt_start_datetime', models.DateTimeField(null=True)),
                ('appt_end_datetime', models.DateTimeField(null=True)),
                ('v_name', models.CharField(null=True)),
                ('v_company', models.CharField(null=True)),
                ('v_desig', models.CharField(null=True)),
                ('v_mobile_no', models.CharField(null=True)),
                ('v_meal', models.CharField(null=True)),
                ('more_info', models.CharField(null=True)),
                ('veh_no', models.CharField(null=True)),
                ('v_asset', models.CharField(null=True)),
                ('reason_for_visit', models.CharField(null=True)),
                ('ppe', models.CharField(null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('delete_flag', models.CharField(default='N', max_length=1, null=True)),
            ],
            options={
                'db_table': 'visitors_management',
            },
        ),
    ]
