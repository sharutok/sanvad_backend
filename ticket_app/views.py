from django.db.models import Q
from rest_framework.response import Response
from rest_framework.decorators import api_view
from ticket_app.models import TicketSystemModel, TicketFileUploadModel
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
from psycopg2.extras import Json

from django.contrib import admin
from datetime import datetime
from django.db import connection


# GET ALL DATA.
@api_view(["GET"])
def all_data(request):
    paginator = PageNumberPagination()
    search_query = request.GET["search"]
    paginator.page_size = 10
    obj = (
        TicketSystemModel.objects.all()
        .filter(
            Q(ticket_no__icontains=search_query)
            | Q(tkt_title__icontains=search_query)
            | Q(tkt_type__icontains=search_query)
        )
        .order_by("-ticket_no")
    )
    result_page = paginator.paginate_queryset(obj, request)
    serializers = TicketSytemSerializer(result_page, many=True)
    return paginator.get_paginated_response(serializers.data)


@api_view(["GET", "PUT", "DELETE"])
def data_by_id(request, id):
    match request.method:
        case "GET":
            obj = TicketSystemModel.objects.get(id=id)
            form_serializers = TicketSytemSerializer(obj)

            user_info = UserManagement.objects.get(
                emp_no=form_serializers.data["requester_emp_no"]
            )
            user_info_serializers = userManagementSerializer(user_info)

            # Define a custom format to parse the datetime string
            date_format = "%Y-%m-%dT%H:%M:%S.%fZ"

            # Parse the datetime string
            datetime_obj = datetime.strptime(
                form_serializers.data["created_at"], date_format
            )

            # Extract date and time components
            date = datetime_obj.date().strftime("%d-%b-%Y")
            time = datetime_obj.time().strftime("%I:%M %p")
            user_info = {
                "Name": user_info_serializers.data["first_name"]
                + " "
                + user_info_serializers.data["last_name"],
                "Department": user_info_serializers.data["department"],
                "Ticket No": form_serializers.data["ticket_no"],
                "Ticket Date": date + " " + time,
                "Employee ID": user_info_serializers.data["emp_no"],
            }

            obj = TicketFileUploadModel.objects.filter(ticket_ref_id=id)
            upload_serializers = TicketFileUploadSerializer(obj, many=True)

            return Response(
                {
                    "user_info": user_info,
                    "form_data": form_serializers.data,
                    "upload_data": upload_serializers.data,
                    "status_code": status.HTTP_200_OK,
                }
            )
        case "PUT":
            try:
                id_value = "{}".format(request.data["id"])
                serializers = TicketSytemSerializer(
                    TicketSystemModel.objects.get(id=request.data["id"])
                )
                approver_detail = user_details_from_emp_id(request.data["user_info"])
                obj_data = {
                    "index": len(serializers.data["approval_flow"]),
                    "status": request.data["approver_status"],
                    "comments": request.data["approver_comment"],
                    "department": approver_detail["department"],
                    "emp_id": (approver_detail["emp_no"]),
                    "user_name": "{} {}".format(
                        approver_detail["first_name"], approver_detail["last_name"]
                    ),
                    "time": datetime.now().strftime("%A, %d %b %Y %H:%M"),
                    "next_approver": "",
                }

                # DEFINE THE SQL QUERY WITH PLACEHOLDERS
                sql = """
                UPDATE tkt_system
                SET approval_flow = approval_flow || %s::jsonb
                WHERE id = %s;
                """
                match len(serializers.data["approval_flow"]):
                    # ticket at manager
                    case 0:
                        approver_emp = request.data["user_info"]
                        user_info = user_details_from_emp_id((json.loads(approver_emp)))

                        obj = TicketSystemModel.objects.get(id=request.data["id"])
                        serializers = TicketSytemSerializer(
                            obj,
                            data={"tkt_current_at": ticket_flow_users("ticket_admin")},
                        )
                        if serializers.is_valid():
                            serializers.save()

                        obj_data["next_approver"] = ticket_flow_users("ticket_admin")
                        with connection.cursor() as cursor:
                            cursor.execute(sql, [Json(obj_data), id_value])
                    # ticket at ticket admin
                    case 1:
                        approver_emp = request.data["user_info"]
                        user_info = user_details_from_emp_id((json.loads(approver_emp)))

                        obj_data["next_approver"] = ticket_flow_users("ticket_admin")

                        with connection.cursor() as cursor:
                            cursor.execute(sql, [Json(obj_data), id_value])
                    case _:
                        print("None")

                # EXECUTE THE QUERY WITH THE DYNAMIC VALUES

                return Response({"results": "ok"})
            except Exception as e:
                print(e)
                return Response(
                    {"status_code": status.HTTP_400_BAD_REQUEST, "error": "error"}
                )

        case "DELETE":
            try:
                TicketSystemModel.objects.filter(id=id).update(delete_flag=True)
                TicketFileUploadModel.objects.filter(ticket_ref_id=id).update(
                    delete_flag=True
                )
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
                return Response(
                    {"mess": "Created Successfully", "status": status.HTTP_200_OK}
                )

            else:
                return Response(
                    {"mess": "error", "status": 400, "error": queryset.errors}
                )
        else:
            print("Ticketserializers", Ticketserializers.errors)
            return Response(
                {"mess": "error", "status": 400, "error": Ticketserializers.errors}
            )
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


# GET_ALL_USER_LIST
@api_view(["GET"])
def get_all_user_list(request):
    raw_sql_query = "select distinct first_name ,last_name ,emp_no,department  from user_management where emp_no in (select distinct(emp_no) from user_management um where user_status=true );"
    with connection.cursor() as cursor:
        cursor.execute(raw_sql_query)
        results = cursor.fetchall()
        return Response(results)


def user_details_from_emp_id(emp_no):
    queryset = UserManagement.objects.get(emp_no=emp_no)
    serializers = userManagementSerializer(queryset)
    return serializers.data


def ticket_flow_users(type):
    r = redis.Redis(host="localhost", port=6379, decode_responses=True)
    data = json.loads(r.get("ticket_wf_systems"))
    emp = ""
    for d in data:
        if d["type"] == type:
            emp = d["user"]
    return emp

    return json.loads(r.get("ticket_wf_systems"))


ticket_wf_status = {0: "INPROGRESS", 1: "APPROVED", 2: "REJECTED"}
