from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.shortcuts import render
from sanvad_app.models import UserManagement
from sanvad_app.serializers import userManagementSerializer
from rest_framework import status
import requests


# GET ALL DATA.
@api_view(["GET"])
def all_data(request):
    obj = UserManagement.objects.all()
    serializers = userManagementSerializer(obj, many=True)
    return Response(serializers.data)


@api_view(["GET", "PUT", "DELETE"])
def data_by_id(request, id):
    match request.method:
        case "GET":
            obj = UserManagement.objects.get(pk=id)
            serializers = userManagementSerializer(obj)
            return Response(
                {"data": serializers.data, "status_code": status.HTTP_200_OK}
            )

        case "PUT":
            obj = UserManagement.objects.get(pk=id)
            serializers = userManagementSerializer(obj, data=request.data)
            if serializers.is_valid():
                serializers.save()
                return Response(
                    {"data": serializers.data, "status_code": status.HTTP_200_OK}
                )
            return Response(
                {
                    "error": serializers.errors,
                    "status_code": status.HTTP_400_BAD_REQUEST,
                }
            )
        case "DELETE":
            obj = UserManagement.objects.get(pk=id)
            obj.delete()
            return Response(
                {"mess": f"Deleted {id}".format(id), "status_code": status.HTTP_200_OK}
            )


# CREATE
@api_view(["POST"])
def create(request):
    serializers = userManagementSerializer(data=request.data)
    if serializers.is_valid():
        serializers.save()
        return Response({"mess": "Created", "status": 200})
    return Response({"mess": "Not", "status": 400, "err": serializers.errors})
