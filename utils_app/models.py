from django.db import models
import uuid

# Create your models here.


class Announsment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=True)
    # announsments_title = models.CharField(max_length=50, null=True)
    announsments_description = models.CharField(max_length=500, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    delete_flag = models.BooleanField(default=False)

    def __str__(self):
        return self.id

    class Meta:
        db_table = "announsments"
