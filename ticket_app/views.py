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
import re


# GET ALL DATA.
@api_view(["GET"])
def all_data(request):
    paginator = PageNumberPagination()
    _search_query = request.GET["search"]
    _emp_no = str(request.GET["woosee"])
    # check if the user is admin or just user
    _emp_no = (
        ""
        if _emp_no == ticket_flow_user_for_systems("ticket_admin_system")
        else _emp_no
    )
    paginator.page_size = 10
    raw_sql_query = """
        select
        ts.*,
        concat(um.first_name, ' ',
        um.last_name) tkt_current_at,
        concat(um2.first_name,' ',
        um2.last_name) requester_emp_name,
        to_char(ts.created_at::timestamp AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata', 'DD-MM-YYYY hh:mi AM') created_at
        from
        	tkt_system ts
        left join user_management um on
        	ts.tkt_current_at = um.emp_no
        left join user_management um2 on
        	ts.requester_emp_no = um2.emp_no 
        	where 
        	(tkt_current_at like '%{}%' 
        	or requester_emp_no like '%{}%')
         and
        	( ticket_no::text like '%{}%'
            or tkt_type like '%{}%'
            or req_type like '%{}%'
            )
            and ts.delete_flag = false
        	order by ts.created_at desc;
    """.format(
        _emp_no,
        _emp_no,
        _search_query,
        _search_query,
        _search_query,
    )
    with connection.cursor() as cursor:
        cursor.execute(raw_sql_query)
        results = cursor.fetchall()
        rows = [
            dict(zip([col[0] for col in cursor.description], row)) for row in results
        ]
    result_page = paginator.paginate_queryset(rows, request)
    return paginator.get_paginated_response(result_page)


@api_view(["GET", "PUT", "DELETE"])
def data_by_id(request, id):
    match request.method:
        case "GET":
            obj = TicketSystemModel.objects.get(id=id)
            form_serializers = TicketSytemSerializer(obj)
            view_access = ticket_components_view_access(
                request.GET["woosee"], form_serializers.data
            )

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
                    "view_access": view_access,
                }
            )
        case "PUT":
            if request.data["tkt_status"] != ticket_wf_status[3]:
                print(request.data["tkt_status"])
                try:
                    id_value = "{}".format(request.data["id"])
                    serializers = TicketSytemSerializer(
                        TicketSystemModel.objects.get(id=request.data["id"])
                    )
                    approver_detail = user_details_from_emp_id(
                        request.data["user_info"]
                    )

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
                    # IF TICKET TYPE IS INFRA
                    match request.data["tkt_type"]:
                        case "IT INFRA":
                            match request.data["req_type"]:
                                case "ISSUES":
                                    match len(serializers.data["approval_flow"]):
                                        # ticket is with admin infra
                                        case 1:
                                            approver_emp = request.data["user_info"]
                                            user_info = user_details_from_emp_id(
                                                approver_emp
                                            )
                                            obj = TicketSystemModel.objects.get(
                                                id=request.data["id"]
                                            )
                                            assign_ticket_to_user = request.data[
                                                "assign_ticket_to_user"
                                            ]
                                            assign_ticket_to_user_id = re.split(
                                                "-", assign_ticket_to_user
                                            )[0]

                                            serializers = TicketSytemSerializer(
                                                obj,
                                                data={
                                                    "tkt_current_at": assign_ticket_to_user_id,
                                                    "tkt_status": ticket_wf_status[0]
                                                    if request.data["approver_status"]
                                                    == "0"
                                                    else ticket_wf_status[2],
                                                },
                                            )

                                            if serializers.is_valid():
                                                serializers.save()

                                            obj_data[
                                                "next_approver"
                                            ] = assign_ticket_to_user_id

                                            with connection.cursor() as cursor:
                                                cursor.execute(
                                                    sql, [Json(obj_data), id_value]
                                                )
                                        # ticket is with technical user
                                        case 2:
                                            approver_emp = request.data["user_info"]
                                            user_info = user_details_from_emp_id(
                                                approver_emp
                                            )
                                            obj = TicketSystemModel.objects.get(
                                                id=request.data["id"]
                                            )
                                            assign_ticket_to_user = request.data[
                                                "assign_ticket_to_user"
                                            ]
                                            assign_ticket_to_user_id = re.split(
                                                "-", assign_ticket_to_user
                                            )[0]

                                            serializers = TicketSytemSerializer(
                                                obj,
                                                data={
                                                    "tkt_current_at": None,
                                                    "tkt_status": ticket_wf_status[3],
                                                },
                                            )

                                            if serializers.is_valid():
                                                serializers.save()

                                            obj_data["next_approver"] = None

                                            with connection.cursor() as cursor:
                                                cursor.execute(
                                                    sql, [Json(obj_data), id_value]
                                                )

                                case "DATACENTER / VPN ACCESS":
                                    match len(serializers.data["approval_flow"]):
                                        # ticket at manager
                                        case 0:
                                            approver_emp = request.data["user_info"]
                                            user_info = user_details_from_emp_id(
                                                (json.loads(approver_emp))
                                            )

                                            obj = TicketSystemModel.objects.get(
                                                id=request.data["id"]
                                            )
                                            serializers = TicketSytemSerializer(
                                                obj,
                                                data={
                                                    "tkt_current_at": ticket_flow_user_for_infra(
                                                        "req1", "ticket_admin_infra"
                                                    ),
                                                    "tkt_status": ticket_wf_status[0]
                                                    if request.data["approver_status"]
                                                    == "0"
                                                    else ticket_wf_status[2],
                                                },
                                            )
                                            if serializers.is_valid():
                                                serializers.save()

                                            obj_data[
                                                "next_approver"
                                            ] = ticket_flow_user_for_systems(
                                                "ticket_admin_system"
                                            )
                                            with connection.cursor() as cursor:
                                                cursor.execute(
                                                    sql, [Json(obj_data), id_value]
                                                )

                                        # ticket at ticket admin
                                        case 1:
                                            approver_emp = request.data["user_info"]
                                            user_info = user_details_from_emp_id(
                                                (json.loads(approver_emp))
                                            )

                                            obj = TicketSystemModel.objects.get(
                                                id=request.data["id"]
                                            )
                                            serializers = TicketSytemSerializer(
                                                obj,
                                                data={
                                                    "tkt_current_at": ticket_flow_user_for_systems(
                                                        "it_head"
                                                    ),
                                                    "tkt_status": ticket_wf_status[0]
                                                    if request.data["approver_status"]
                                                    == "0"
                                                    else ticket_wf_status[2],
                                                    "severity": request.data[
                                                        "severity"
                                                    ],
                                                },
                                            )
                                            if serializers.is_valid():
                                                serializers.save()

                                            obj_data[
                                                "next_approver"
                                            ] = ticket_flow_user_for_systems("it_head")
                                            with connection.cursor() as cursor:
                                                cursor.execute(
                                                    sql, [Json(obj_data), id_value]
                                                )

                                        # ticket is at it head
                                        case 2:
                                            approver_emp = request.data["user_info"]
                                            user_info = user_details_from_emp_id(
                                                approver_emp
                                            )
                                            obj = TicketSystemModel.objects.get(
                                                id=request.data["id"]
                                            )
                                            assign_ticket_to_user = request.data[
                                                "assign_ticket_to_user"
                                            ]
                                            assign_ticket_to_user_id = re.split(
                                                "-", assign_ticket_to_user
                                            )[0]

                                            serializers = TicketSytemSerializer(
                                                obj,
                                                data={
                                                    "tkt_current_at": assign_ticket_to_user_id,
                                                    "tkt_status": ticket_wf_status[0]
                                                    if request.data["approver_status"]
                                                    == "0"
                                                    else ticket_wf_status[2],
                                                },
                                            )

                                            if serializers.is_valid():
                                                serializers.save()

                                            obj_data[
                                                "next_approver"
                                            ] = assign_ticket_to_user_id

                                            with connection.cursor() as cursor:
                                                cursor.execute(
                                                    sql, [Json(obj_data), id_value]
                                                )

                                            # ticket is with technical user
                                        case 3:
                                            approver_emp = request.data["user_info"]
                                            user_info = user_details_from_emp_id(
                                                approver_emp
                                            )
                                            obj = TicketSystemModel.objects.get(
                                                id=request.data["id"]
                                            )
                                            assign_ticket_to_user = request.data[
                                                "assign_ticket_to_user"
                                            ]
                                            assign_ticket_to_user_id = re.split(
                                                "-", assign_ticket_to_user
                                            )[0]

                                            serializers = TicketSytemSerializer(
                                                obj,
                                                data={
                                                    "tkt_current_at": None,
                                                    "tkt_status": ticket_wf_status[3],
                                                },
                                            )

                                            if serializers.is_valid():
                                                serializers.save()

                                            obj_data["next_approver"] = None

                                            with connection.cursor() as cursor:
                                                cursor.execute(
                                                    sql, [Json(obj_data), id_value]
                                                )

                        case _:
                            match len(serializers.data["approval_flow"]):
                                # ticket at manager
                                case 0:
                                    approver_emp = request.data["user_info"]
                                    user_info = user_details_from_emp_id(
                                        (json.loads(approver_emp))
                                    )

                                    obj = TicketSystemModel.objects.get(
                                        id=request.data["id"]
                                    )
                                    serializers = TicketSytemSerializer(
                                        obj,
                                        data={
                                            "tkt_current_at": ticket_flow_user_for_systems(
                                                "ticket_admin_system"
                                            ),
                                            "tkt_status": ticket_wf_status[0]
                                            if request.data["approver_status"] == "0"
                                            else ticket_wf_status[2],
                                        },
                                    )
                                    if serializers.is_valid():
                                        serializers.save()

                                    obj_data[
                                        "next_approver"
                                    ] = ticket_flow_user_for_systems(
                                        "ticket_admin_system"
                                    )
                                    with connection.cursor() as cursor:
                                        cursor.execute(sql, [Json(obj_data), id_value])

                                # ticket at ticket admin
                                case 1:
                                    approver_emp = request.data["user_info"]
                                    user_info = user_details_from_emp_id(
                                        (json.loads(approver_emp))
                                    )

                                    obj = TicketSystemModel.objects.get(
                                        id=request.data["id"]
                                    )
                                    serializers = TicketSytemSerializer(
                                        obj,
                                        data={
                                            "tkt_current_at": ticket_flow_user_for_systems(
                                                "it_head"
                                            ),
                                            "tkt_status": ticket_wf_status[0]
                                            if request.data["approver_status"] == "0"
                                            else ticket_wf_status[2],
                                            "severity": request.data["severity"],
                                        },
                                    )
                                    print(request.data)
                                    if serializers.is_valid():
                                        obj = serializers.save()
                                        n = str(request.data["file_count"])
                                        if n >= "0":
                                            for i in range(0, int(n)):
                                                file = "file{}".format(i + 1)
                                                data = {
                                                    "ticket_ref_id": obj.id,
                                                    "user_file": request.data[file],
                                                    "filename": request.data[file],
                                                }
                                                queryset = TicketFileUploadSerializer(
                                                    data=data
                                                )
                                                if queryset.is_valid():
                                                    queryset.save()

                                    obj_data[
                                        "next_approver"
                                    ] = ticket_flow_user_for_systems("it_head")
                                    with connection.cursor() as cursor:
                                        cursor.execute(sql, [Json(obj_data), id_value])

                                # ticket is at it head
                                case 2:
                                    approver_emp = request.data["user_info"]
                                    user_info = user_details_from_emp_id(approver_emp)
                                    obj = TicketSystemModel.objects.get(
                                        id=request.data["id"]
                                    )
                                    assign_ticket_to_user = request.data[
                                        "assign_ticket_to_user"
                                    ]
                                    assign_ticket_to_user_id = re.split(
                                        "-", assign_ticket_to_user
                                    )[0]

                                    serializers = TicketSytemSerializer(
                                        obj,
                                        data={
                                            "tkt_current_at": assign_ticket_to_user_id,
                                            "tkt_status": ticket_wf_status[0]
                                            if request.data["approver_status"] == "0"
                                            else ticket_wf_status[2],
                                        },
                                    )

                                    if serializers.is_valid():
                                        serializers.save()

                                    obj_data["next_approver"] = assign_ticket_to_user_id

                                    with connection.cursor() as cursor:
                                        cursor.execute(sql, [Json(obj_data), id_value])

                                    # ticket is with technical user
                                case 3:
                                    approver_emp = request.data["user_info"]
                                    user_info = user_details_from_emp_id(approver_emp)
                                    obj = TicketSystemModel.objects.get(
                                        id=request.data["id"]
                                    )
                                    assign_ticket_to_user = request.data[
                                        "assign_ticket_to_user"
                                    ]
                                    assign_ticket_to_user_id = re.split(
                                        "-", assign_ticket_to_user
                                    )[0]

                                    serializers = TicketSytemSerializer(
                                        obj,
                                        data={
                                            "tkt_current_at": None,
                                            "tkt_status": ticket_wf_status[3],
                                        },
                                    )

                                    if serializers.is_valid():
                                        serializers.save()

                                    obj_data["next_approver"] = None

                                    with connection.cursor() as cursor:
                                        cursor.execute(sql, [Json(obj_data), id_value])

                                case _:
                                    print("None")

                    # IF TICKET TYPE IS SYSTEMS

                    # EXECUTE THE QUERY WITH THE DYNAMIC VALUES

                    return Response({"status_code": status.HTTP_200_OK})
                    # return Response({"status_code": 202})
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

        # whose your manager
        user_info = UserManagement.objects.get(emp_no=requester_emp_no)
        Userserializers = userManagementSerializer(user_info)
        users_manager = Userserializers.data["manager_code"]
        _data = {}
        match request.data["tkt_type"]:
            case "IT INFRA":
                if request.data["req_type"] == "ISSUES":
                    _data["tkt_current_at"] = ticket_flow_user_for_infra(
                        "req1", "ticket_admin_infra"
                    )
                else:
                    _data["tkt_current_at"] = users_manager

        Ticketserializers = TicketSytemSerializer(
            data={
                "tkt_current_at": users_manager,
                "tkt_title": request.data["tkt_title"],
                "tkt_type": request.data["tkt_type"],
                "req_type": request.data["req_type"],
                "tkt_description": request.data["tkt_description"],
                "requester_emp_no": request.data["requester_emp_no"],
            }
        )
        if Ticketserializers.is_valid():
            obj = Ticketserializers.save()
            # UPLOAD FILE LOGIC
            n = str(request.data["file_count"])
            if n >= "0":
                print(n)
                for i in range(0, int(n)):
                    file = "file{}".format(i + 1)
                    data = {
                        "ticket_ref_id": obj.id,
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
            print(Ticketserializers.errors)
            return Response({"mess": "error", "status": "300"})

    except Exception as e:
        print("error", e)
        return Response({"mess": "error", "status": 400, "err": e})


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


def ticket_flow_user_for_systems(type):
    r = redis.Redis(host="localhost", port=6379, decode_responses=True)
    data = json.loads(r.get("ticket_wf_systems"))
    emp = ""
    for d in data:
        if d["type"] == type:
            emp = d["user"]
    return emp

    return json.loads(r.get("ticket_wf_systems"))


def ticket_flow_user_for_infra(req, type):
    r = redis.Redis(host="localhost", port=6379, decode_responses=True)
    data = json.loads(r.get("ticket_wf_infra"))
    emp = ""
    for dat in data:
        for key, value in dat.items():
            if key == req:
                for val in value:
                    if val["type"] == type:
                        emp = val["user"]
    print(emp)
    return emp


ticket_wf_status = {0: "INPROGRESS", 1: "APPROVED", 2: "REJECTED", 3: "CLOSED"}


def ticket_components_view_access(woosee, request):
    components = {
        "assign_ticket_comp": False,
        "status_close": False,
        "upload_documents": False,
        "approval_status": False,
        "submit_btn": False,
        "comments_box": False,
        "severity_component": False,
    }

    components["assign_ticket_comp"] = (
        True if str(ticket_flow_user_for_systems("it_head")) == str(woosee) else False
    )
    components["submit_btn"] = (
        True if str(request["requester_emp_no"]) != str(woosee) else False
    )
    components["approval_status"] = (
        True if str(request["requester_emp_no"]) != str(woosee) else False
    )
    components["comments_box"] = (
        True if str(request["requester_emp_no"]) != str(woosee) else False
    )
    components["upload_documents"] = (
        True
        if str(
            ticket_flow_user_for_systems("ticket_admin_system")
            or ticket_flow_user_for_infra("req1", "ticket_admin_infra")
        )
        == str(woosee)
        else False
    )
    components["severity_component"] = (
        True
        if str(
            ticket_flow_user_for_systems("ticket_admin_system")
            or ticket_flow_user_for_infra("req1", "ticket_admin_infra")
        )
        == str(woosee)
        else False
    )
    return components
