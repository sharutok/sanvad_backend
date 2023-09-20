from django.contrib.postgres.fields import ArrayField
from conference_app.models import ConferenceBooking
from rest_framework import serializers
import uuid


class ConferenceBookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConferenceBooking
        fields = "__all__"
