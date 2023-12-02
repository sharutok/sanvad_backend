from django.db.models import Q
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.shortcuts import render
from visitors_app.models import VisitorsManagement, VisitorPhoto
from visitors_app.serializers import (
    VisitorsManagementSerializer,
    VisitorPhotoSerializer,
)
from rest_framework import status
import requests
from datetime import datetime
from rest_framework.pagination import PageNumberPagination
from django.db import connection
import json
import redis
from io import BytesIO
import base64, binascii
import os
from django.core.files.base import ContentFile


# GET ALL DATA.
@api_view(["GET"])
def all_data(request):
    paginator = PageNumberPagination()
    search_query = request.GET["search"]
    woosee = "" if request.GET["woosee"] in security_det() else request.GET["woosee"]

    paginator.page_size = 10
    raw_sql_query = """select
	vm.*,
	concat(um.first_name,
	' ',
	um.last_name)name,
	um.department,
	to_char(vm.start_date_time ::timestamp ,
	'DD-MM-YYYY hh:mi AM') mod_start_date_time ,
	to_char(vm.end_date_time ::timestamp ,
	'DD-MM-YYYY hh:mi AM') mod_end_date_time
    from
    	visitors_management vm
    left join user_management um on
	vm.raised_by = um.emp_no
    where vm.raised_by like '%{}%' and  vm.delete_flag=false and  (vm.reason_for_visit like '%{}%' or vm.raised_by like '%{}%' ) order by updated_at desc;""".format(
        woosee, search_query, search_query
    )

    with connection.cursor() as cursor:
        cursor.execute(raw_sql_query)
        results = cursor.fetchall()
        rows = [
            dict(zip([col[0] for col in cursor.description], row)) for row in results
        ]

    result_page = paginator.paginate_queryset(rows, request)
    return paginator.get_paginated_response(result_page)


# GET DATA BY ID
# DELETE DATA BY ID
@api_view(["GET", "DELETE", "PUT"])
def data_by_id(request, id):
    match request.method:
        case "GET":
            woosee = request.GET["woosee"]
            raw_sql_query = """
                            select
                            	vm.*,
                            	concat(um.first_name,' ',um.last_name)name,
                            	um.department 
                            from
                            	visitors_management vm
                            left join user_management um on
                            	vm.raised_by = um.emp_no
                            where vm.id='{}'	
                            ;""".format(
                id
            )
            view_access = visitor_components_view_access(woosee, id)
            with connection.cursor() as cursor:
                cursor.execute(raw_sql_query)
                results = cursor.fetchall()
                rows = [
                    dict(zip([col[0] for col in cursor.description], row))
                    for row in results
                ]
            return Response(
                {
                    "data": rows,
                    "status_code": status.HTTP_200_OK,
                    "view_access": view_access,
                },
            )
        case "DELETE":
            try:
                VisitorsManagement.objects.filter(id=id).update(delete_flag=True)
                return Response(
                    {
                        "status_code": status.HTTP_200_OK,
                    }
                )
            except Exception as e:
                return Response(
                    {
                        "status_code": status.HTTP_400_BAD_REQUEST,
                    }
                )
        case "PUT":
            try:
                obj = VisitorsManagement.objects.get(pk=id)
                request.data["visitors"] = json.loads(request.data["visitors"])
                serializers = VisitorsManagementSerializer(obj, data=request.data)
                if serializers.is_valid():
                    serializers.save()
                    return Response(
                        {
                            "status_code": status.HTTP_200_OK,
                        }
                    )

            except Exception as e:
                return Response(
                    {
                        "status_code": status.HTTP_400_BAD_REQUEST,
                    }
                )


@api_view(["POST"])
def save_image(request):
    try:
        _data = request.data["byteArray"]
        image_name = request.data["image_name"]
        base64_string = str(_data).split(",")[1]
        image_data = base64.b64decode(base64_string, validate=True)
        VisitorPhoto_instance = VisitorPhoto(
            name=image_name, visitor_pass_id=image_name.split("__")[0]
        )
        VisitorPhoto_instance.image.save(f"{image_name}.png", ContentFile(image_data))
        return Response({"status_code": status.HTTP_200_OK})
    except Exception as e:
        print(e)
        return Response({"status_code": status.HTTP_400_BAD_REQUEST})


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


@api_view(["GET"])
def get_image(request):
    try:
        id = request.GET["id"]
        querydata = VisitorPhoto.objects.filter(visitor_pass_id=id)
        serializers = VisitorPhotoSerializer(querydata, many=True)
        return Response({"data": serializers.data, "status": status.HTTP_200_OK})
    except Exception as e:
        return Response(
            {
                "mess": e,
                "status": status.HTTP_400_BAD_REQUEST,
            }
        )


@api_view(["PUT"])
def punch(request):
    try:
        id = request.GET["id"]
        print(request.data)
        dataObj = {}
        for data in request.data:
            if request.data[data]:
                dataObj[data] = request.data[data]

        obj = VisitorsManagement.objects.get(pk=id)
        serializers = VisitorsManagementSerializer(obj, data=dataObj)
        if serializers.is_valid():
            serializers.save()
        return Response(
            {
                "status_code": status.HTTP_200_OK,
            }
        )
    except Exception as e:
        print(e)
        return Response(
            {
                "status_code": status.HTTP_400_BAD_REQUEST,
            }
        )


def visitor_components_view_access(woosee, id):
    queryset = VisitorsManagement.objects.get(pk=id)
    serializers = VisitorsManagementSerializer(queryset)

    components = {
        "print_component": False,
        "camera_component": False,
        "update_btn": False,
        "punch_in": False,
        "punch_out": False,
        "delete_btn": False,
    }
    components["print_component"] = True if woosee in security_det() else False
    components["camera_component"] = True if woosee in security_det() else False

    def update_btn():
        if str(serializers.data["visitor_status"]) == str(0):
            return True
        else:
            return False

    components["update_btn"] = update_btn()

    def punch():
        if not serializers.data["punch_in_date_time"]:
            return [True, False]

        if serializers.data["punch_in_date_time"]:
            if (
                serializers.data["punch_in_date_time"]
                and serializers.data["punch_out_date_time"]
            ):
                return [False, False]
            return [False, True]

    val = punch()
    components["punch_in"] = val[0]
    components["punch_out"] = val[1]

    return components


@api_view(["GET"])
def visitor_list_component_view_access(request):
    try:
        components = {
            "delete_btn": False,
        }
        woosee = request.GET["woosee"]
        components["delete_btn"] = True if woosee in security_det() else False
        return Response(components)
    except Exception as e:
        return Response(
            {
                "status_code": status.HTTP_400_BAD_REQUEST,
            }
        )


def security_det():
    r = redis.Redis(host="localhost", port=6379, decode_responses=True)
    key_name = "security_admin"
    return r.lrange(key_name, 0, -1)
