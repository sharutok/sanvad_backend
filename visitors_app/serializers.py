from django.contrib.postgres.fields import ArrayField
from visitors_app.models import VisitorsManagement
from rest_framework import serializers
import uuid


class VisitorsManagementSerializer(serializers.ModelSerializer):
    class Meta:
        model = VisitorsManagement
        fields = "__all__"
