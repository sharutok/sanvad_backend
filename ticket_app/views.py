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

from sanvad_project.settings import r
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
    emp_no = str(request.GET["woosee"])

    # check if the user is admin or just user
    _emp_no = (
        ""
        if (
            emp_no == ticket_flow_user_for_systems("ticket_admin_system")
            or emp_no == ticket_flow_user_for_infra("req1", "ticket_admin_infra")
        )
        else emp_no
    )

    _tkt_type = ""
    if not _emp_no:
        if str(emp_no) == str(ticket_flow_user_for_systems("ticket_admin_system")):
            _tkt_type = "IT SYSTEMS(ERP ORACLE)"
        if str(emp_no) == str(ticket_flow_user_for_infra("req1", "ticket_admin_infra")):
            _tkt_type = "IT INFRA"

    def _req_type():
        if not _emp_no:
            if str(_emp_no) == str(ticket_flow_user_for_systems("ticket_admin_system")):
                return "IT SYSTEMS(ERP ORACLE)"
            if str(_emp_no) == str(
                ticket_flow_user_for_infra("req1", "ticket_admin_infra")
            ):
                return "IT INFRA"

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
        	((tkt_current_at like '%{}%' 
        	or requester_emp_no like '%{}%') and tkt_type like '%{}%')
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
        _tkt_type,
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
                "Email ID": user_info_serializers.data["email_id"],
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
                # print(request.data["tkt_status"])
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

                    def res_body_for_erp_tkt(user_status, nextflow):
                        tkt_status = ""
                        tkt_current_at = ""
                        # APPROVED
                        if user_status == "0":
                            if len(serializers.data["approval_flow"]) >= 3:
                                tkt_status = ticket_wf_status[0]
                                tkt_current_at = nextflow
                            else:
                                tkt_status = ticket_wf_status[0]
                                tkt_current_at = nextflow
                        # REJECTED
                        if user_status == "1":
                            tkt_status = ticket_wf_status[2]
                            tkt_current_at = None

                        # CLOSED
                        if user_status == "2":
                            tkt_status = ticket_wf_status[3]
                            tkt_current_at = None
                            obj_data["status"] = "2"

                        return [tkt_status, tkt_current_at]

                    def res_body_for_infr_tkt_wf1(user_status, nextflow):
                        tkt_status = ""
                        tkt_current_at = ""
                        # APPROVED
                        if user_status == "0":
                            if len(serializers.data["approval_flow"]) == 3:
                                tkt_status = ticket_wf_status[3]
                                tkt_current_at = None
                                obj_data["status"] = "2"
                            else:
                                tkt_status = ticket_wf_status[0]
                                tkt_current_at = nextflow
                        # REJECTED
                        if user_status == "1":
                            tkt_status = ticket_wf_status[2]
                            tkt_current_at = None
                        return [tkt_status, tkt_current_at]

                    obj = TicketSystemModel.objects.get(id=request.data["id"])
                    approver_emp = request.data["user_info"]

                    def res_body_for_infra_tkt_wf2(user_status, nextflow):
                        tkt_status = ""
                        tkt_current_at = ""
                        match request.data["req_type"]:
                            case "ISSUES":
                                # APPROVED
                                if user_status == "0":
                                    if len(serializers.data["approval_flow"]) == 0:
                                        tkt_status = ticket_wf_status[0]
                                        tkt_current_at = nextflow
                                        # tkt_current_at = "C0072"
                                    if len(serializers.data["approval_flow"]) == 1:
                                        obj_data["status"] = "2"
                                        tkt_status = ticket_wf_status[3]
                                        tkt_current_at = None
                                # REJECTED
                                if user_status == "1":
                                    tkt_status = ticket_wf_status[2]
                                    tkt_current_at = None

                        return [tkt_status, tkt_current_at]

                    # get ticket data based on id

                    def approval_flow_execute(obj_data):
                        try:
                            with connection.cursor() as cursor:
                                cursor.execute(sql, [Json(obj_data), id_value])
                        except Exception as e:
                            print("approval_flow_execute", e)

                    # IF TICKET TYPE IS INFRA
                    match request.data["tkt_type"]:
                        case "IT INFRA":
                            match request.data["req_type"]:
                                case "ISSUES":
                                    match len(serializers.data["approval_flow"]):
                                        # ticket is with admin infra
                                        case 0:
                                            val = res_body_for_infra_tkt_wf2(
                                                request.data["approver_status"],
                                                redis_get_string(
                                                    "it_infra_issues_technical"
                                                ),
                                            )

                                            serializers = TicketSytemSerializer(
                                                obj,
                                                data={
                                                    "tkt_status": val[0],
                                                    "tkt_current_at": val[1],
                                                },
                                            )
                                            obj_data["next_approver"] = val[1]

                                            if serializers.is_valid():
                                                serializers.save()
                                            approval_flow_execute(obj_data)

                                        # ticket is with technical user
                                        case 1:
                                            val = res_body_for_infra_tkt_wf2(
                                                request.data["approver_status"],
                                                "",
                                            )
                                            serializers = TicketSytemSerializer(
                                                obj,
                                                data={
                                                    "tkt_status": val[0],
                                                    "tkt_current_at": val[1],
                                                },
                                            )
                                            obj_data["next_approver"] = val[1]

                                            if serializers.is_valid():
                                                serializers.save()
                                            approval_flow_execute(obj_data)

                                case "DATACENTER / VPN ACCESS":
                                    match len(serializers.data["approval_flow"]):
                                        # ticket at manager
                                        case 0:
                                            val = res_body_for_infr_tkt_wf1(
                                                request.data["approver_status"],
                                                ticket_flow_user_for_infra(
                                                    "req1", "ticket_admin_infra"
                                                ),
                                            )

                                            serializers = TicketSytemSerializer(
                                                obj,
                                                data={
                                                    "tkt_status": val[0],
                                                    "tkt_current_at": val[1],
                                                },
                                            )
                                            obj_data["next_approver"] = val[1]

                                            if serializers.is_valid():
                                                serializers.save()

                                            approval_flow_execute(obj_data)

                                        # ticket at ticket admin
                                        case 1:
                                            val = res_body_for_infr_tkt_wf1(
                                                request.data["approver_status"],
                                                ticket_flow_user_for_systems("it_head"),
                                            )

                                            serializers = TicketSytemSerializer(
                                                obj,
                                                data={
                                                    "tkt_status": val[0],
                                                    "tkt_current_at": val[1],
                                                    "severity": request.data[
                                                        "severity"
                                                    ],
                                                },
                                            )
                                            obj_data["next_approver"] = val[1]

                                            if serializers.is_valid():
                                                serializers.save()
                                            approval_flow_execute(obj_data)

                                        # ticket is at it head
                                        case 2:
                                            assign_ticket_to_user = request.data[
                                                "assign_ticket_to_user"
                                            ]
                                            assign_ticket_to_user_id = re.split(
                                                "-", assign_ticket_to_user
                                            )[0]

                                            val = res_body_for_infr_tkt_wf1(
                                                request.data["approver_status"],
                                                assign_ticket_to_user_id,
                                            )
                                            print(val)

                                            serializers = TicketSytemSerializer(
                                                obj,
                                                data={
                                                    "tkt_status": val[0],
                                                    "tkt_current_at": val[1],
                                                },
                                            )
                                            obj_data["next_approver"] = val[1]

                                            if serializers.is_valid():
                                                serializers.save()
                                            approval_flow_execute(obj_data)

                                            # ticket is with technical user
                                        case 3:
                                            val = res_body_for_infr_tkt_wf1(
                                                request.data["approver_status"],
                                                "",
                                            )
                                            serializers = TicketSytemSerializer(
                                                obj,
                                                data={
                                                    "tkt_status": val[0],
                                                    "tkt_current_at": val[1],
                                                },
                                            )
                                            obj_data["next_approver"] = None
                                            if serializers.is_valid():
                                                serializers.save()
                                            approval_flow_execute(obj_data)

                        case _:
                            match len(serializers.data["approval_flow"]):
                                # ticket at manager
                                case 0:
                                    user_info = user_details_from_emp_id(
                                        (json.loads(approver_emp))
                                    )

                                    val = res_body_for_erp_tkt(
                                        request.data["approver_status"],
                                        ticket_flow_user_for_systems(
                                            "ticket_admin_system"
                                        ),
                                    )
                                    serializers = TicketSytemSerializer(
                                        obj,
                                        data={
                                            "tkt_status": val[0],
                                            "tkt_current_at": val[1],
                                        },
                                    )
                                    if serializers.is_valid():
                                        serializers.save()
                                        obj_data["next_approver"] = val[1]
                                        approval_flow_execute(obj_data)
                                    else:
                                        print(serializers.errors)

                                # ticket at ticket admin
                                case 1:
                                    user_info = user_details_from_emp_id(
                                        (json.loads(approver_emp))
                                    )

                                    val = res_body_for_erp_tkt(
                                        request.data["approver_status"],
                                        ticket_flow_user_for_systems("it_head"),
                                    )

                                    serializers = TicketSytemSerializer(
                                        obj,
                                        data={
                                            "tkt_status": val[0],
                                            "tkt_current_at": val[1],
                                            "severity": request.data["severity"],
                                            "req_type": request.data["req_type"],
                                            "tkt_description": request.data[
                                                "tkt_description"
                                            ],
                                        },
                                    )

                                    # FILE UPLAOD LOGIC
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
                                                else:
                                                    print(
                                                        "queryset.errors",
                                                        queryset.errors,
                                                    )
                                    else:
                                        print("serializers.errors", serializers.errors)

                                    obj_data["next_approver"] = val[0]
                                    print(val)
                                    print(obj_data)
                                    approval_flow_execute(obj_data)

                                # ticket is at it head
                                case 2:
                                    user_info = user_details_from_emp_id(approver_emp)
                                    assign_ticket_to_user = request.data[
                                        "assign_ticket_to_user"
                                    ]
                                    assign_ticket_to_user_id = re.split(
                                        "-", assign_ticket_to_user
                                    )[0]
                                    val = res_body_for_erp_tkt(
                                        request.data["approver_status"],
                                        assign_ticket_to_user_id,
                                    )

                                    serializers = TicketSytemSerializer(
                                        obj,
                                        data={
                                            "tkt_status": val[0],
                                            "tkt_current_at": val[1],
                                        },
                                    )
                                    obj_data["next_approver"] = val[0]

                                    if serializers.is_valid():
                                        serializers.save()
                                    approval_flow_execute(obj_data)

                                    # ticket is with technical user

                                # technical user
                                case _:
                                    if len(serializers.data["approval_flow"]) >= 2:
                                        assign_ticket_to_user = request.data[
                                            "assign_ticket_to_user"
                                        ]
                                        assign_ticket_to_user_id = re.split(
                                            "-", assign_ticket_to_user
                                        )[0]

                                        val = res_body_for_erp_tkt(
                                            request.data["approver_status"],
                                            assign_ticket_to_user_id,
                                        )

                                        serializers = TicketSytemSerializer(
                                            obj,
                                            data={
                                                "tkt_status": val[0],
                                                "tkt_current_at": val[1],
                                            },
                                        )

                                        obj_data["next_approver"] = val[1]

                                        # FILE UPLAOD LOGIC
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
                                                    queryset = (
                                                        TicketFileUploadSerializer(
                                                            data=data
                                                        )
                                                    )
                                                    if queryset.is_valid():
                                                        queryset.save()
                                                    else:
                                                        print(
                                                            "queryset.errors",
                                                            queryset.errors,
                                                        )
                                        else:
                                            print(
                                                "serializers.errors", serializers.errors
                                            )
                                        approval_flow_execute(obj_data)

                    return Response({"status_code": status.HTTP_200_OK})
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

        _data = {"tkt_current_at": users_manager}
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
                "tkt_current_at": _data["tkt_current_at"],
                "tkt_title": request.data["tkt_title"],
                "tkt_type": request.data["tkt_type"],
                "req_type": request.data["req_type"],
                "tkt_description": request.data["tkt_description"],
                "requester_emp_no": request.data["requester_emp_no"],
            }
        )
        print(Ticketserializers)
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
    ##r = redis.Redis(host="localhost", port=6379, decode_responses=True)
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
    ##r = redis.Redis(host="localhost", port=6379, decode_responses=True)
    key_name = "requirement_type"
    index = request.data["index"]
    key_name = "{}_{}".format(key_name, index)
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
    woosee = request.GET["woosee"]
    raw_sql_query = "select distinct first_name ,last_name ,emp_no,department from user_management where department ='INFORMATION TECHNOLOGY' and emp_no !='{}';".format(
        woosee
    )
    with connection.cursor() as cursor:
        cursor.execute(raw_sql_query)
        results = cursor.fetchall()
        return Response(results)


def user_details_from_emp_id(emp_no):
    queryset = UserManagement.objects.get(emp_no=emp_no)
    serializers = userManagementSerializer(queryset)
    return serializers.data


def ticket_flow_user_for_systems(type):
    ##r = redis.Redis(host="localhost", port=6379, decode_responses=True)
    data = json.loads(r.get("ticket_wf_systems"))
    emp = ""
    for d in data:
        if d["type"] == type:
            emp = d["user"]
    return emp

    return json.loads(r.get("ticket_wf_systems"))


def ticket_flow_user_for_infra(req, type):
    ##r = redis.Redis(host="localhost", port=6379, decode_responses=True)
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
        "close_radio_btn": False,
    }

    components["close_radio_btn"] = (
        True if len(request["approval_flow"]) >= 3 else False
    )
    components["assign_ticket_comp"] = (
        True
        if (
            str(ticket_flow_user_for_systems("it_head")) == str(woosee)
            or len(request["approval_flow"]) >= 3
        )
        else False
    )

    def submit_btn():
        if str(request["tkt_current_at"]) != str(woosee):
            return False
        else:
            return True

    components["submit_btn"] = submit_btn()

    components["approval_status"] = (
        True if str(request["tkt_current_at"]) == str(woosee) else False
    )

    components["comments_box"] = (
        True if str(request["tkt_current_at"]) == str(woosee) else False
    )

    components["upload_documents"] = (
        True
        if (
            str(
                ticket_flow_user_for_systems("ticket_admin_system")
                or ticket_flow_user_for_infra("req1", "ticket_admin_infra")
            )
            == str(woosee)
            or (
                True
                if (
                    (len(request["approval_flow"])) >= 3
                    and str(request["tkt_current_at"]) == str(woosee)
                )
                else False
            )
        )
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


def redis_get_string(key):
    try:
        ##r = redis.Redis(host="localhost", port=6379, decode_responses=True)
        dt = r.get(key)
        return dt
    except Exception as e:
        print("error", e)
        return Response({"error": e})
