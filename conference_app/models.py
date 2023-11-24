from django.contrib.postgres.fields import ArrayField
from django.db import models
import uuid

# Create your models here.


class ConferenceBooking(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=True)
    conf_by = models.CharField(max_length=50, null=True)
    meeting_about = models.CharField(max_length=50, null=True)
    conf_start_date = models.DateField(null=True)
    conf_start_time = models.TimeField(null=True)
    conf_end_date = models.DateField(null=True)
    disp_conf_end_date = models.DateField(null=True)
    conf_end_time = models.TimeField(null=True)
    conf_room = models.CharField(max_length=50, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    delete_flag = models.BooleanField(default=False)

    def __str__(self):
        return self.id

    class Meta:
        db_table = "conference_booking"
