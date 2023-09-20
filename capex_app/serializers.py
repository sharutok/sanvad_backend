from django.contrib.postgres.fields import ArrayField
from capex_app.models import Capex, Capex1
from rest_framework import serializers
import uuid


class CapexSerializer(serializers.ModelSerializer):
    class Meta:
        model = Capex
        fields = "__all__"


class Capex1Serializer(serializers.ModelSerializer):
    class Meta:
        model = Capex1
        fields = "__all__"
