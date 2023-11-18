from django.contrib.postgres.fields import ArrayField
from capex_app.models import Capex, Capex1, UploadBudget
from rest_framework import serializers
import uuid


class CapexSerializer(serializers.ModelSerializer):
    class Meta:
        model = Capex
        fields = "__all__"


class Capex1Serializer(serializers.ModelSerializer):
    mod_file_path = serializers.SerializerMethodField()
    mod_file_name = serializers.SerializerMethodField()

    class Meta:
        model = Capex1
        fields = "__all__"

    def get_mod_file_path(self, object):
        return str("http://localhost:8000/media/" + str(object.user_file))

    def get_mod_file_name(self, object):
        return str(object.user_file).split("/")[-1]


class UploadBudgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadBudget
        fields = "__all__"
