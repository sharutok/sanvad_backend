from django.db.models import Q
from rest_framework.response import Response
from rest_framework.decorators import api_view
from sanvad_app.models import UserManagement
from sanvad_app.serializers import userManagementSerializer
from rest_framework import status
import requests
from rest_framework.pagination import PageNumberPagination
from datetime import datetime
from django.db import connection
import json
import redis
import bcrypt


# GET ALL DATA.
@api_view(["GET"])
def all_data(request):
    search_query = request.GET["search"]
    paginator = PageNumberPagination()
    paginator.page_size = 10
    obj = (
        UserManagement.objects.all()
        .filter(
            Q(first_name__icontains=search_query)
            | Q(last_name__icontains=search_query)
            | Q(department__icontains=search_query)
            | Q(last_name__icontains=search_query)
            | Q(emp_no__icontains=search_query)
        )
        .order_by("-updated_at")
    )

    result_page = paginator.paginate_queryset(obj, request)
    serializers = userManagementSerializer(result_page, many=True)
    return paginator.get_paginated_response(serializers.data)


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
                print(request.data)
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


# VERIFY USER
@api_view(["POST"])
def login_verify_user(request):
    try:
        email = request.data["email"] + request.data["prefix"]
        password = request.data["password"]

        if email:
            queryset_email = UserManagement.objects.filter(email_id=email)

            if queryset_email.exists():
                queryset_email = UserManagement.objects.get(email_id=email)
                serializers = userManagementSerializer(queryset_email)

                hashed_password_from_database = serializers.data["password"].encode(
                    "utf-8"
                )
                provided_password = password.encode("utf-8")

                if bcrypt.checkpw(provided_password, hashed_password_from_database):
                    return Response(
                        {
                            "status": status.HTTP_200_OK,
                            "emp_no": serializers.data["emp_no"],
                            "module_permission": serializers.data["module_permission"],
                            "initials": str(serializers.data["first_name"])[0:1]
                            + str(serializers.data["last_name"])[0:1],
                        },
                    )
                else:
                    return Response({"status": HTTP_400_BAD_REQUEST})
            else:
                return Response({"status": HTTP_400_BAD_REQUEST})
    except Exception as e:
        print(e, "error")
        return Response({"status": status.HTTP_404_NOT_FOUND})


@api_view(["GET"])
def birthday_list(request):
    try:
        r = redis.Redis(host="localhost", port=6379, decode_responses=True)
        return Response({"data": json.loads(r.get("todays_birthday"))})
    except e:
        print("error", e)
        return Response({"error": e})


# DYNAMIC VALUES- user_permission
@api_view(["POST", "GET", "DELETE"])
def user_permission_dynamic_values(request):
    r = redis.Redis(host="localhost", port=6379, decode_responses=True)
    key_name = "user_permission"
    match request.method:
        # ALL DATA
        case "GET":
            data = r.lrange(key_name, 0, -1)
            return Response(data)
        # CREATE
        case "POST":
            r.lpush(key_name, request.data["value"].upper())
            data = r.lrange(key_name, 0, -1)
            return Response(data)
        # DELETE
        case "DELETE":
            r.lrem(key_name, 0, request.data["value"])
            data = r.lrange(key_name, 0, -1)
            return Response(data)
