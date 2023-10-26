from django.contrib.postgres.fields import ArrayField
from visitors_app.models import VisitorsManagement
from rest_framework import serializers
import uuid


class VisitorsManagementSerializer(serializers.ModelSerializer):
    class ObjectSerializer(serializers.ModelSerializer):
        start_date_time = serializers.DateTimeField(format="%d-%m-%Y %H:%M:%S")
        end_date_time = serializers.DateTimeField(format="%d-%m-%Y %H:%M:%S")

    class Meta:
        model = VisitorsManagement
        fields = "__all__"
