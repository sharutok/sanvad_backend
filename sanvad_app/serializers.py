from django.contrib.postgres.fields import ArrayField
from sanvad_app.models import UserManagement
from rest_framework import serializers
import uuid


class userManagementSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserManagement
        fields = "__all__"
        # exclude=["id"]

    # def create(self,object):
    #     return True
