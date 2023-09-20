from django.db import models
from django.contrib.postgres.fields import ArrayField
import uuid

# Create your models here.


def upload_path(instance, filename):
    return "/".join(["ticket", str(instance.id), filename])


class TicketSystemModel(models.Model):
    # id = models.UUIDField(default=uuid.uuid4, editable=True)
    id = models.UUIDField(null=True)
    requester_emp_no = models.CharField(max_length=20, null=True)
    ticket_no = models.AutoField(primary_key=True)
    tkt_title = models.CharField(max_length=50, null=True)
    tkt_type = models.CharField(max_length=50, null=True)
    req_type = models.CharField(max_length=50, null=True)
    tkt_description = models.CharField(max_length=50, null=True)
    tkt_date = models.CharField(max_length=50, null=True)
    tkt_status = models.CharField(max_length=50, null=True)
    tkt_current_at = models.CharField(max_length=50, null=True)
    tkt_docs = ArrayField(models.CharField(max_length=150), null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approver_1_emp_no = models.CharField(max_length=50, null=True)
    approver_1_status = models.CharField(max_length=100, null=True)
    approver_2_emp_no = models.CharField(max_length=50, null=True)
    approver_2_status = models.CharField(max_length=100, null=True)
    approver_3_emp_no = models.CharField(max_length=50, null=True)
    approver_3_status = models.CharField(max_length=100, null=True)

    def __str__(self):
        return self.id

    class Meta:
        db_table = "tkt_system"


class TicketFileUploadModel(models.Model):
    id = models.UUIDField(primary_key=True)
    ticket_ref_id = models.UUIDField(editable=True)
    file_name = models.CharField(max_length=100, null=True)
    user_file = models.FileField(blank=True, null=True, upload_to=upload_path)

    def __str__(self):
        return self.id

    class Meta:
        db_table = "tkt_file_uploads"
