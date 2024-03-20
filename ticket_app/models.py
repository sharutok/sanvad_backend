from django.db import models
from django.contrib.postgres.fields import ArrayField, JSONField
import uuid

# Create your models here.


def upload_path(instance, filename):
    return "/".join(["ticket", str(instance.id), filename])


class TicketSystemModel(models.Model):
    id = models.UUIDField(default=uuid.uuid4, editable=True)
    requester_emp_no = models.CharField(max_length=20, null=True)
    ticket_no = models.AutoField(primary_key=True)
    tkt_title = models.CharField(max_length=500, null=True)
    tkt_type = models.CharField(max_length=50, null=True)
    req_type = models.CharField(max_length=50, null=True)
    tkt_description = models.CharField(max_length=1000, null=True)
    tkt_status = models.CharField(max_length=50, null=True, default="INPROGRESS")
    tkt_current_at = models.CharField(max_length=50, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    severity = models.IntegerField(default=0)
    delete_flag = models.BooleanField(default=False)
    approval_flow = models.JSONField(default=list)

    def __str__(self):
        return self.id

    class Meta:
        db_table = "tkt_system"


class TicketFileUploadModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=True)
    ticket_ref_id = models.UUIDField(editable=True)
    file_name = models.CharField(max_length=100, null=True)
    user_file = models.FileField(blank=True, null=True, upload_to=upload_path)
    delete_flag = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.ticket_ref_id

    class Meta:
        db_table = "tkt_file_uploads"
