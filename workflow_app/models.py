from django.db import models
import uuid
from django.contrib.postgres.fields import ArrayField, JSONField

class CapexWorkflow(models.Model):
    id = models.UUIDField( default=uuid.uuid4, editable=True)
    department=models.CharField(primary_key=True,max_length=100)
    which_flow=models.CharField(max_length=100,null=True)
    approver= models.JSONField(default=list)
    # first_approver=models.CharField(null=True)
    # second_approver=models.CharField(null=True)
    # third_approver=models.CharField(null=True)
    # fourth_approver=models.CharField(null=True)
    notify_user=models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.id
    
    class Meta:
        db_table='capex_workflow'
