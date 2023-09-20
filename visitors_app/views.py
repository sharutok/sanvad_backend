from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.shortcuts import render
from visitors_app.models import VisitorsManagement
from visitors_app.serializers import VisitorsManagementSerializer
from rest_framework import status
import requests
from datetime import datetime


# GET ALL DATA.
@api_view(["GET"])
def all_data(request):
    obj = VisitorsManagement.objects.all()
    serializers = VisitorsManagementSerializer(obj, many=True)
    return Response({"data": [serializers.data]})


# GET DATA BY ID
# DELETE DATA BY ID
@api_view(["GET", "DELETE"])
def data_by_id(request, id):
    match request.method:
        case "GET":
            obj = VisitorsManagement.objects.get(pk=id)
            serializers = VisitorsManagementSerializer(obj)
            return Response(
                {"data": [serializers.data], "status_code": status.HTTP_200_OK}
            )
        case "DELETE":
            obj = VisitorsManagement.objects.get(pk=id)
            request.data["delete_flag"] = "Y"
            serializers = VisitorsManagementSerializer(obj, data=request.data)
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


# CREATE
@api_view(["POST"])
def create(request):
    serializers = VisitorsManagementSerializer(data=request.data)
    if serializers.is_valid():
        serializers.save()
        return Response({"mess": "Created", "status": 200})
    return Response({"mess": "Not", "status": 400, "err": serializers.errors})
