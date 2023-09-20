from django.contrib.postgres.fields import ArrayField
from ticket_app.models import TicketSystemModel, TicketFileUploadModel
from rest_framework import serializers
import uuid


class TicketSytemSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketSystemModel
        fields = "__all__"


class TicketFileUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketFileUploadModel
        fields = "__all__"
