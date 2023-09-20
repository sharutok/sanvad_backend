from rest_framework.response import Response
from rest_framework.decorators import api_view
from ticket_app.models import TicketSystemModel
from ticket_app.serializers import (
    TicketSytemSerializer,
    TicketFileUploadSerializer,
)

from sanvad_app.models import UserManagement
from sanvad_app.serializers import userManagementSerializer

from rest_framework import status
import requests
from rest_framework.pagination import PageNumberPagination

import redis
import json
import uuid

from django.contrib import admin


# GET ALL DATA.
@api_view(["GET"])
def all_data(request):
    paginator = PageNumberPagination()
    paginator.page_size = 10
    obj = TicketSystemModel.objects.all()
    result_page = paginator.paginate_queryset(obj, request)
    serializers = TicketSytemSerializer(result_page, many=True)
    return paginator.get_paginated_response(serializers.data)


"""
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

"""


# CREATE NEW TICKET
@api_view(["POST"])
def create(request):
    try:
        _ticket_ref_id = uuid.uuid4()
        requester_emp_no = request.data["requester_emp_no"]
        user_info = UserManagement.objects.get(emp_no=requester_emp_no)
        Userserializers = userManagementSerializer(user_info)

        request.data["tkt_current_at"] = Userserializers.data["manager_code"]
        request.data["approver_1_emp_no"] = Userserializers.data["manager_code"]
        request.data["id"] = _ticket_ref_id
        request.data["tkt_status"] = ticket_wf_status[0]

        Ticketserializers = TicketSytemSerializer(data=request.data)

        if Ticketserializers.is_valid():
            Ticketserializers.save()
        # UPLOAD FILE LOGIC
        n = str(request.data["file_count"])
        for i in range(0, int(n)):
            file = "file{}".format(i + 1)
            data = {
                "id": uuid.uuid4(),
                "ticket_ref_id": _ticket_ref_id,
                "user_file": request.data[file],
                "filename": request.data[file],
            }
            queryset = TicketFileUploadSerializer(data=data)
            if queryset.is_valid():
                queryset.save()
            response = Response(
                {"mess": "Created Successfully", "status": status.HTTP_201_CREATED}
            )
        return response

    except Exception as e:
        print({"mess": "error", "status": 400, "err": e})
        return Response({"mess": "error", "status": 400, "err": e})

    # ADD DATA


# DYNAMIC VALUES- ticket_type
@api_view(["POST", "GET", "DELETE"])
def ticket_type_dynamic_values(request):
    r = redis.Redis(host="localhost", port=6379, decode_responses=True)
    key_name = "ticket_type"
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


# DYNAMIC VALUES- requirement_type
@api_view(["POST", "PUT", "DELETE"])
def req_type_dynamic_values(request):
    r = redis.Redis(host="localhost", port=6379, decode_responses=True)
    key_name = "requirement_type"
    index = request.data["index"]
    key_name = "{}:{}".format(key_name, index)
    match request.method:
        # GET ALL DATA
        case "POST":
            data = r.lrange(key_name, 0, -1)
            return Response(data)
        # CREATE
        case "PUT":
            r.lpush(key_name, request.data["value"].upper())
            data = r.lrange(key_name, 0, -1)
            return Response(data)
        # DELETE
        case "DELETE":
            r.lrem(key_name, 0, request.data["value"])
            data = r.lrange(key_name, 0, -1)
            return Response(data)


ticket_wf_status = {0: "INPROGRESS", 1: "APPROVED", 2: "REJECTED"}
