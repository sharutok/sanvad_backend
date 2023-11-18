from django.contrib.postgres.fields import ArrayField
from policies_app.models import UploadPolicy
from rest_framework import serializers
import uuid
from datetime import datetime


class UploadPolicySerializer(serializers.ModelSerializer):
    mod_created_at = serializers.SerializerMethodField()
    mod_file_path = serializers.SerializerMethodField()
    mod_file_name = serializers.SerializerMethodField()

    class Meta:
        model = UploadPolicy
        fields = "__all__"

    def get_mod_created_at(self, object):
        return datetime.fromisoformat(str(object.created_at)).strftime("%d-%m-%Y")

    def get_mod_file_path(self, object):
        return str("http://localhost:8000/media/" + str(object.policy_file))

    def get_mod_file_name(self, object):
        return str(object.policy_file).split("/")[-1]
