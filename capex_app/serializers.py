from django.contrib.postgres.fields import ArrayField
from capex_app.models import Capex
from rest_framework import serializers
import uuid


class CapexSerializer(serializers.ModelSerializer):
    class Meta:
        model = Capex
        fields = "__all__"
        # exclude=["id"]
