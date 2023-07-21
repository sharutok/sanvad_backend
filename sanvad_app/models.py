from django.contrib.postgres.fields import ArrayField
from django.db import models
import uuid

# Create your models here.


class UserManagement(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=True)
    first_name = models.CharField(max_length=50, null=True)
    last_name = models.CharField(max_length=50, null=True)
    ph_no = models.CharField(max_length=15, null=True)
    dob = models.DateField(null=True)
    gender = models.IntegerField(null=True)
    emerg_contact = models.CharField(max_length=15, null=True)
    address = models.CharField(max_length=50, null=True)
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True)
    emp_no = models.IntegerField(null=True)
    department = models.IntegerField(null=True)
    plant_name = models.IntegerField(null=True)
    manager = models.IntegerField(null=True)
    job_type = models.IntegerField(null=True)
    employment_type = models.IntegerField(null=True)
    emp_designation = models.CharField(max_length=50, null=True)
    organization = models.IntegerField(null=True)
    email_id = models.CharField(max_length=50, null=True)
    password = models.CharField(max_length=100, null=True)
    user_status = models.BooleanField(default=False)
    user_role = models.IntegerField(null=True)
    module_permission = ArrayField(models.CharField(max_length=15), null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.first_name
