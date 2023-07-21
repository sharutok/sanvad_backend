# Generated by Django 4.2.3 on 2023-07-07 19:27

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    dependencies = [
        ("sanvad_app", "0002_alter_usermanagement_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="usermanagement",
            name="ed_date",
            field=models.DateField(null=True),
        ),
        migrations.AddField(
            model_name="usermanagement",
            name="emerg_contact",
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name="usermanagement",
            name="emp_desig",
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name="usermanagement",
            name="emp_no",
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name="usermanagement",
            name="employment_type",
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name="usermanagement",
            name="first_name",
            field=models.CharField(max_length=50, null=True),
        ),
        migrations.AddField(
            model_name="usermanagement",
            name="gender",
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name="usermanagement",
            name="job_type",
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name="usermanagement",
            name="last_name",
            field=models.CharField(max_length=50, null=True),
        ),
        migrations.AddField(
            model_name="usermanagement",
            name="manager",
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name="usermanagement",
            name="password",
            field=models.CharField(max_length=50, null=True),
        ),
        migrations.AddField(
            model_name="usermanagement",
            name="ph_no",
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name="usermanagement",
            name="plant_name",
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name="usermanagement",
            name="st_date",
            field=models.DateField(null=True),
        ),
        migrations.AddField(
            model_name="usermanagement",
            name="u_dob",
            field=models.DateField(null=True),
        ),
        migrations.AddField(
            model_name="usermanagement",
            name="user_address",
            field=models.CharField(max_length=50, null=True),
        ),
        migrations.AddField(
            model_name="usermanagement",
            name="user_department",
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name="usermanagement",
            name="user_email_id",
            field=models.CharField(max_length=50, null=True),
        ),
        migrations.AddField(
            model_name="usermanagement",
            name="user_role",
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name="usermanagement",
            name="user_stat",
            field=models.IntegerField(null=True),
        ),
        migrations.AlterField(
            model_name="usermanagement",
            name="id",
            field=models.UUIDField(
                default=uuid.uuid4, primary_key=True, serialize=False
            ),
        ),
    ]
