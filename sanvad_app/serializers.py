from django.contrib.postgres.fields import ArrayField
from sanvad_app.models import UserManagement
from rest_framework import serializers
import uuid


class userManagementSerializer(serializers.ModelSerializer):
    len_module_permission = serializers.SerializerMethodField()

    class Meta:
        model = UserManagement
        fields = "__all__"
        # exclude=["id"]

    def get_len_module_permission(self, object):
        if len(object.module_permission):
            return len(object.module_permission)
        else:
            return 0
