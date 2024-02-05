from django.db import models
import uuid
from django.contrib.postgres.fields import ArrayField


def upload_path(instance, filename):
    return "/".join(["capex", str(instance.id), filename])


def budget_upload_path(instance, filename):
    return "/".join(["budget_upload", str(instance.id), filename])


class Capex(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=True)
    budget_no = models.CharField(max_length=200, null=True)
    purpose_code = models.CharField(max_length=200, null=True)
    purpose_description = models.CharField(max_length=200, null=True)
    line_no = models.IntegerField(null=True)
    plant = models.CharField(max_length=200, null=True)
    dept = models.CharField(max_length=200, null=True)
    capex_group = models.CharField(max_length=200, null=True)
    capex_class = models.CharField(max_length=200, null=True)
    category = models.CharField(max_length=200, null=True)
    asset_description = models.CharField(max_length=200, null=True)
    details = models.CharField(max_length=200, null=True)
    rate = models.FloatField(null=True)
    qty = models.FloatField(null=True)
    uom = models.CharField(max_length=200, null=True)
    final_budget = models.FloatField(null=True)
    remarks = models.CharField(max_length=200, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    delete_flag = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return self.budget_no

    class Meta:
        db_table = "capex_excel_master"


class Capex1(models.Model):
    id = models.UUIDField(primary_key=True,default=uuid.uuid4, editable=True)
    budget_id = models.UUIDField(editable=True)
    nature_of_requirement = models.CharField(max_length=150, null=True)
    purpose = models.CharField(max_length=150, null=True)
    payback_period = models.CharField(max_length=150, null=True)
    return_on_investment = models.CharField(max_length=150, null=True)
    budget_type = models.CharField(max_length=150, null=True)
    requisition_date = models.DateField(null=True)
    total_cost = models.FloatField(null=True)
    site_delivery_date = models.DateField(null=True)
    capex_status = models.CharField(max_length=150, null=True)
    installation_date = models.DateField(null=True)
    comment1 = models.CharField(max_length=300, null=True)
    comment2 = models.CharField(max_length=300, null=True)
    comment3 = models.CharField(max_length=300, null=True)
    comment4 = models.CharField(max_length=300, null=True)
    comment5 = models.CharField(max_length=300, null=True)
    comment6 = models.CharField(max_length=300, null=True)
    comment7 = models.CharField(max_length=300, null=True)
    user_file = models.FileField(blank=True, null=True, upload_to=upload_path)
    comment6 = models.CharField(max_length=150, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    asset_listings = models.CharField(max_length=1000, null=True)
    flow_type = models.CharField(max_length=150, null=True)
    approval_flow = models.JSONField(default=list)
    capex_raised_by = models.CharField(max_length=150, null=True)
    capex_current_at = models.CharField(max_length=150, null=True)
    delete_flag = models.BooleanField(default=False)

    def __str__(self):
        return self.id

    class Meta:
        db_table = "capex_data_master"


class UploadBudget(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=True)
    budget_file = models.FileField(blank=True, null=True, upload_to=budget_upload_path)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.budget_file

    class Meta:
        db_table = "upload_budget"
