from django.db import models
import uuid
from django.contrib.postgres.fields import ArrayField, JSONField


class CapexWorkflow(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    plant = models.CharField(max_length=100, blank=True, null=True)
    which_flow = models.CharField(max_length=100)
    approver = models.JSONField(default=list)
    notify_user = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.id

    class Meta:
        db_table = "capex_workflow"
