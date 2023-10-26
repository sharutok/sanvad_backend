from django.db.models import Q
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.shortcuts import render
from visitors_app.models import VisitorsManagement
from visitors_app.serializers import VisitorsManagementSerializer
from rest_framework import status
import requests
from datetime import datetime
from rest_framework.pagination import PageNumberPagination


# GET ALL DATA.
@api_view(["GET"])
def all_data(request):
    paginator = PageNumberPagination()
    search_query = request.GET["search"]
    paginator.page_size = 10
    obj = (
        VisitorsManagement.objects.all()
        .filter(
            Q(reason_for_visit__icontains=search_query)
            | Q(raised_by__icontains=search_query)
        )
        .order_by("-updated_at")
    )
    result_page = paginator.paginate_queryset(obj, request)
    serializers = VisitorsManagementSerializer(result_page, many=True)
    return paginator.get_paginated_response(serializers.data)


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
        return Response({"mess": "Created", "status": status.HTTP_200_OK})
    return Response(
        {
            "mess": "Not",
            "status": status.HTTP_400_BAD_REQUEST,
            "err": serializers.errors,
        }
    )
