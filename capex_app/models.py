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

    def __str__(self):
        return self.id

    class Meta:
        db_table = "capex"
