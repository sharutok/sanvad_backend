from utils_app.models import Announsment
from rest_framework import serializers


class AnnounsmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Announsment
        fields = "__all__"
