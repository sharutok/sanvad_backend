from django.contrib.postgres.fields import ArrayField
from django.db import models
import uuid

# Create your models here.


class UserManagement(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=True)
    first_name = models.CharField(max_length=150, null=True)
    last_name = models.CharField(max_length=150, null=True)
    ph_no = models.CharField(max_length=150, null=True)
    dob = models.CharField(max_length=150, null=True)
    gender = models.CharField(max_length=150, null=True)
    emerg_contact = models.CharField(max_length=150, null=True)
    address = models.CharField(max_length=150, null=True)
    start_date = models.CharField(max_length=150, null=True)
    end_date = models.CharField(max_length=150, null=True)
    emp_no = models.CharField(max_length=150, null=True)
    department = models.CharField(max_length=150, null=True)
    plant_name = models.CharField(max_length=150, null=True)
    manager_code = models.CharField(max_length=150, null=True)
    manager = models.CharField(max_length=150, null=True)
    ess_function = models.CharField(max_length=150, null=True)
    ess_location = models.CharField(max_length=150, null=True)
    cost_code = models.CharField(max_length=150, null=True)
    cost_center_desc = models.CharField(max_length=150, null=True)
    job_status = models.CharField(max_length=150, null=True)
    emp_designation = models.CharField(max_length=150, null=True)
    organization = models.CharField(max_length=150, null=True)
    email_id = models.CharField(max_length=150, null=True)
    password = models.CharField(max_length=150, null=True)
    user_status = models.BooleanField(default=False)
    user_role = models.CharField(max_length=150, null=True)
    module_permission = ArrayField(models.CharField(max_length=150), null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.first_name

    class Meta:
        db_table = "user_management"


class EmployeeMappings(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=True)
    ess_function = models.CharField(max_length=150, null=True)
    ess_location = models.CharField(max_length=150, null=True)
    department = models.CharField(max_length=150, null=True)
    plant_name = models.CharField(max_length=150, null=True)

    def __str__(self):
        return self.ess_function

    class Meta:
        db_table = "employee_mappings"
