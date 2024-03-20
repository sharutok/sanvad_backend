from django.contrib.postgres.fields import ArrayField
from .models import CapexWorkflow
from rest_framework import serializers
import uuid



class CapexWorkflowSerializer(serializers.ModelSerializer):
    class Meta:
        model = CapexWorkflow
        fields = "__all__"
