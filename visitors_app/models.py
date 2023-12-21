from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import JSONField

import uuid

# Create your models here.


def upload_path(instance, filename):
    return "/".join(["visitor_photo", str(instance.visitor_pass_id), filename])


class VisitorsManagement(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=True)
    start_date_time = models.DateTimeField(null=True)
    end_date_time = models.DateTimeField(null=True)
    v_company = models.CharField(null=True)
    raised_by = models.CharField(null=True)
    reason_for_visit = models.CharField(null=True)
    more_info = models.CharField(null=True, blank=True)
    veh_no = models.CharField(null=True, blank=True)
    ppe = models.CharField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    delete_flag = models.BooleanField(default=False)
    visitors = JSONField(default=list, null=True, blank=True)
    punch_in_date_time = models.DateTimeField(null=True)
    punch_out_date_time = models.DateTimeField(null=True)
    visitor_status = models.IntegerField(null=True, default=0)

    def __str__(self):
        return self.id

    class Meta:
        db_table = "visitors_management"


class VisitorPhoto(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=True)
    visitor_pass_id = models.UUIDField(editable=True)
    name = models.CharField(max_length=255, null=True)
    image = models.ImageField(upload_to=upload_path)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    delete_flag = models.BooleanField(default=False)

    def __str__(self):
        return self.id

    class Meta:
        db_table = "visitors_photo_master"
