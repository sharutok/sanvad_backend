from django.db import models
import uuid


def policy_upload_path(instance, filename):
    return "/".join(["policy_upload", str(instance.id), filename])


# Create your models here.
class UploadPolicy(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=True)
    policy_file = models.FileField(blank=True, null=True, upload_to=policy_upload_path)
    policy_type = models.CharField(max_length=50, null=True)
    policy_name = models.CharField(max_length=50, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.policy_file

    class Meta:
        db_table = "policy_master"
