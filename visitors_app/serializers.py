from django.contrib.postgres.fields import ArrayField
from visitors_app.models import VisitorsManagement, VisitorPhoto
from rest_framework import serializers
from sanvad_project.settings import FILE_SERVE_LINK


class VisitorsManagementSerializer(serializers.ModelSerializer):
    class ObjectSerializer(serializers.ModelSerializer):
        start_date_time = serializers.DateTimeField(format="%d-%m-%Y %H:%M:%S")
        end_date_time = serializers.DateTimeField(format="%d-%m-%Y %H:%M:%S")

    class Meta:
        model = VisitorsManagement
        fields = "__all__"


class VisitorPhotoSerializer(serializers.ModelSerializer):
    mod_image = serializers.SerializerMethodField()

    class Meta:
        model = VisitorPhoto
        fields = "__all__"
        fields = ["mod_image", "name"]

    def get_mod_image(self, object):
        return str(FILE_SERVE_LINK + str(object.image))
