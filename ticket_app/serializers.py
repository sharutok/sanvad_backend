from django.contrib.postgres.fields import ArrayField
from ticket_app.models import TicketSystemModel, TicketFileUploadModel
from rest_framework import serializers
import uuid


class TicketSytemSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketSystemModel
        fields = "__all__"


class TicketFileUploadSerializer(serializers.ModelSerializer):
    mod_file_path = serializers.SerializerMethodField()
    mod_file_name = serializers.SerializerMethodField()

    class Meta:
        model = TicketFileUploadModel
        fields = "__all__"

    def get_mod_file_path(self, object):
        return str("http://localhost:8000/media/" + str(object.user_file))

    def get_mod_file_name(self, object):
        return str(object.user_file).split("/")[-1]
