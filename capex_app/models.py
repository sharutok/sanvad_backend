from django.contrib.postgres.fields import ArrayField
from django.db import models
import uuid


class Capex(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=True)
    budget_no = models.CharField(max_length=50, null=True)
    purpose_code = models.CharField(max_length=50, null=True)
    purpose_description = models.CharField(max_length=50, null=True)
    line_no = models.IntegerField(null=True)
    plant = models.CharField(max_length=50, null=True)
    dept = models.CharField(max_length=50, null=True)
    capex_group = models.CharField(max_length=50, null=True)
    capex_class = models.CharField(max_length=50, null=True)
    category = models.CharField(max_length=50, null=True)
    asset_description = models.CharField(max_length=50, null=True)
    details = models.CharField(max_length=50, null=True)
    rate = models.IntegerField(null=True)
    qty = models.IntegerField(null=True)
    uom = models.CharField(max_length=50, null=True)
    final_budget = models.IntegerField(null=True)
    remarks = models.CharField(max_length=50, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.budget_no

    class Meta:
        db_table = "capex_excel_master"


class Capex1(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=True)
    # capex_id = models.UUIDField(editable=True)
    nature_of_requirement = models.CharField(max_length=50, null=True)
    purpose = models.CharField(max_length=50, null=True)
    payback_period = models.CharField(max_length=50, null=True)
    return_on_investment = models.CharField(max_length=50, null=True)
    budget_type = models.CharField(max_length=50, null=True)
    requisition_date = models.DateField(null=True)
    total_cost = models.IntegerField(null=True)
    site_delivery_date = models.DateField(null=True)
    installation_date = models.DateField(null=True)
    comment1 = models.CharField(max_length=100, null=True)
    comment2 = models.CharField(max_length=100, null=True)
    comment3 = models.CharField(max_length=100, null=True)
    comment4 = models.CharField(max_length=100, null=True)
    comment5 = models.CharField(max_length=100, null=True)
    comment6 = models.CharField(max_length=100, null=True)
    comment7 = models.CharField(max_length=100, null=True)
    attachment_file_name = models.CharField(max_length=100, null=True)
    attachment_loc_path_name = models.CharField(max_length=100, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.capex_id

    class Meta:
        db_table = "capex_data_master"
