import smtplib
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

from django.db.models import Q
from rest_framework.response import Response
from rest_framework.decorators import api_view
from ticket_app.models import TicketSystemModel, TicketFileUploadModel
from sanvad_app.models import UserManagement
from ticket_app.serializers import (
    TicketSytemSerializer,
    TicketFileUploadSerializer,
)
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
          case 
        	when tkt_current_at='00547' and jsonb_array_length(approval_flow)=0 then 'MANAGER' 
        	when tkt_current_at='00547' and jsonb_array_length(approval_flow)=2 then 'IT HEAD' 
        	when tkt_current_at='14383' and jsonb_array_length(approval_flow)=1 then 'TICKET ADMIN' 
        	else ''
        end as ROLE,
        concat(um.first_name, ' ',
        um.last_name) tkt_current_at,
        concat(um2.first_name,' ',um2.last_name) requester_emp_name,
        case
		when tkt_status = 'CLOSED' then replace(approval_flow[jsonb_array_length(approval_flow)-1]['time']::text,'"',' ')
		end as closed_date,
		case
		when tkt_status = 'CLOSED' then replace(approval_flow[jsonb_array_length(approval_flow)-1]['user_name']::text,'"',' ')
		end as closed_by,
        to_char(ts.created_at::timestamp AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata', 'DD-MM-YYYY hh:mi AM') created_at,
        coalesce(COUNT(tfu.ticket_ref_id),0) as total_file_uploads
        from
        	tkt_system ts
        left join user_management um on
        	ts.tkt_current_at = um.emp_no
        left join user_management um2 on
        	ts.requester_emp_no = um2.emp_no 
        left join  tkt_file_uploads tfu on
			ts.id = tfu.ticket_ref_id
        	where 
        	((tkt_current_at like '%{}%' 
        	or requester_emp_no like '%{}%') and tkt_type like '%{}%')
         and
        	( ticket_no::text like '%{}%'
            or tkt_type ilike '%{}%'
            or req_type ilike '%{}%'
            or tkt_title ilike '%{}%'
            or um.first_name ilike '%{}%' 
            or um.last_name ilike '%{}%'
            or um2.first_name ilike '%{}%' 
            or um2.last_name ilike '%{}%'
            or tkt_status ilike '%{}%'
            )
            and ts.delete_flag = false
            group by
		    ts.id,
		    ts.ticket_no,
		    ts.tkt_title,
		    ts.tkt_type ,
		    ts.req_type ,
		    ts.tkt_description ,
		    um.first_name,
		    um.last_name,
		    um2.first_name,
		    um2.last_name
        	order by ts.created_at desc
         ;
    """.format(
        _emp_no,
        _emp_no,
        _tkt_type,
        _search_query,
        _search_query,
        _search_query,
        _search_query,
        _search_query,
        _search_query,
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


@api_view(["GET"])
def view_all_tickets(request):
    paginator = PageNumberPagination()
    _search_query = request.GET["search"]

    # check if the user is admin or just user

    paginator.page_size = 10

    raw_sql_query = """
        select
        ts.*,
          case 
        	when tkt_current_at='00547' and jsonb_array_length(approval_flow)=0 then 'MANAGER' 
        	when tkt_current_at='00547' and jsonb_array_length(approval_flow)=2 then 'IT HEAD' 
        	when tkt_current_at='14383' and jsonb_array_length(approval_flow)=1 then 'TICKET ADMIN' 
        	else ''
        end as ROLE,
        concat(um.first_name, ' ',
        um.last_name) tkt_current_at,
        concat(um2.first_name,' ',
        um2.last_name) requester_emp_name,
        to_char(ts.created_at::timestamp AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata', 'DD-MM-YYYY hh:mi AM') created_at,
        coalesce(COUNT(tfu.ticket_ref_id),0) as total_file_uploads,
         case
		when tkt_status = 'CLOSED' then replace(approval_flow[jsonb_array_length(approval_flow)-1]['time']::text,'"',' ')
		end as closed_date,
		case
		when tkt_status = 'CLOSED' then replace(approval_flow[jsonb_array_length(approval_flow)-1]['user_name']::text,'"',' ')
		end as closed_by
        from
        	tkt_system ts
        left join user_management um on
        	ts.tkt_current_at = um.emp_no
        left join user_management um2 on
        	ts.requester_emp_no = um2.emp_no 
        left join  tkt_file_uploads tfu on
			ts.id = tfu.ticket_ref_id
        	where 
        	( ticket_no::text ilike '%{}%'
            or tkt_type ilike '%{}%'
            or req_type ilike '%{}%'
            or um.first_name ilike '%{}%' 
            or um.last_name ilike '%{}%'
            or um2.first_name ilike '%{}%' 
            or um2.last_name ilike '%{}%'
            or tkt_status ilike '%{}%'
            )
            and ts.delete_flag = false
            group by
		    ts.id,
		    ts.ticket_no,
		    ts.tkt_title,
		    ts.tkt_type ,
		    ts.req_type ,
		    ts.tkt_description ,
		    um.first_name,
		    um.last_name,
		    um2.first_name,
		    um2.last_name
        	order by ts.created_at desc
         ;
    """.format(
        _search_query,
        _search_query,
        _search_query,
        _search_query,
        _search_query,
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
                request.GET["woosee"], form_serializers.data, request.GET["qreuecs"]
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
                # "Ticket Date": date + " " + time,
                "Ticket Date": form_serializers.data["created_at"],
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
                                            assign_ticket_to_user = request.data[
                                                "assign_ticket_to_user"
                                            ]
                                            assign_ticket_to_user_id = re.split(
                                                "-", assign_ticket_to_user
                                            )[0]

                                            val = res_body_for_infra_tkt_wf2(
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
                                        instance = serializers.save()
                                        obj_data["next_approver"] = val[1]
                                        approval_flow_execute(obj_data)
                                        send_mail_later(
                                            obj_data=obj_data, instance=instance
                                        )
                                    else:
                                        print(serializers.errors)

                                # ticket at ticket admin
                                case 1:
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
                                        obj_data["next_approver"] = val[0]
                                        approval_flow_execute(obj_data)
                                        send_mail_later(obj_data=obj_data, instance=obj)
                                    else:
                                        print("serializers.errors", serializers.errors)

                                # ticket is at it head
                                case 2:
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
                                        instance = serializers.save()
                                        approval_flow_execute(obj_data)
                                        send_mail_later(
                                            obj_data=obj_data, instance=instance
                                        )

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
                                            approval_flow_execute(obj_data)
                                            send_mail_later(
                                                obj_data=obj_data,
                                                instance=obj,
                                            )
                                        else:
                                            print(
                                                "serializers.errors", serializers.errors
                                            )

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
        if Ticketserializers.is_valid():
            obj = Ticketserializers.save()
            send_mail_early(instance=obj)
            # UPLOAD FILE LOGIC
            n = str(request.data["file_count"])
            if n >= "0":
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
    return emp


ticket_wf_status = {0: "INPROGRESS", 1: "APPROVED", 2: "REJECTED", 3: "CLOSED"}


def ticket_components_view_access(woosee, request, qreuecs):
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
    if not qreuecs:
        components["close_radio_btn"] = (
            True if len(request["approval_flow"]) >= 3 else False
        )

        components["assign_ticket_comp"] = (
            True
            if (
                (
                    str(ticket_flow_user_for_systems("it_head")) == str(woosee)
                    and len(request["approval_flow"]) == 2
                )
                or len(request["approval_flow"]) >= 3
                or (
                    str(ticket_flow_user_for_infra("req1", "ticket_admin_infra"))
                    == str(woosee)
                    and len(request["approval_flow"]) == 1
                )
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
                (
                    ticket_flow_user_for_systems("ticket_admin_system") == str(woosee)
                    and len(request["approval_flow"]) == 1
                )
                or (
                    ticket_flow_user_for_infra("req1", "ticket_admin_infra")
                    == str(woosee)
                    and len(request["approval_flow"]) == 0
                )
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


def send_mail_later(obj_data, instance):
    try:
        mail_status = ["APPROVED", "REJECTED", "CLOSED"]
        _data = {
            "current_approver_status": mail_status[int(obj_data["status"])],
            "raised_by_mail_id": user_details_from_emp_id(instance.requester_emp_no)[
                "email_id"
            ],
            "next_approver_mail_id": ""
            if not instance.tkt_current_at
            else user_details_from_emp_id(instance.tkt_current_at)["email_id"],
            "current_approved_by": user_details_from_emp_id(obj_data["emp_id"])[
                "first_name"
            ]
            + " "
            + user_details_from_emp_id(obj_data["emp_id"])["last_name"],
            "current_approver_comment": obj_data["comments"],
            "ticket_raised_by": user_details_from_emp_id(instance.requester_emp_no)[
                "first_name"
            ]
            + " "
            + user_details_from_emp_id(instance.requester_emp_no)["last_name"],
            "ticket_no": instance.ticket_no,
            "title": instance.tkt_title,
            "requirement_type": instance.req_type,
            "ticket_link": instance.id,
        }
        load_dotenv()
        subject = "Adorhub - Ticket Notification"
        from_email = os.getenv("SENDER_EMAIL")
        smtp_server = os.getenv("SMTP_SERVER")
        smtp_port = os.getenv("SMTP_PORT")
        smtp_username = os.getenv("SMTP_USERNAME")
        smtp_password = os.getenv("SMTP_PASSWORD")
        tkt_link_prefix = os.getenv("TICKET_LINK_PREFIX")

        html = """
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <link href='https://fonts.googleapis.com/css?family=Source+Sans+Pro' rel='stylesheet' type='text/css'>
                    <meta charset="UTF-8">
                    <meta http-equiv="X-UA-Compatible" content="IE=edge">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                </head>
                <body style="padding: 1rem; font-family: 'Source Sans Pro', sans-serif;">
                    <div style="display: flex;">
                        <div style="width: 600px; margin-top: 1rem; display: grid; grid-template-columns: auto; gap: 2rem; width:fit-content;border-radius: 10px;padding:2rem;">
                            <img src="https://adorwelding.org/Adorhub_uploads/Ticket.png" width="800" alt="Conference Header" style="display: flex;justify-content: center;">
                            <div style="color: #555259; padding: 0 2rem;">
                                <div >
                                    <span style="font-size: 2rem; font-weight: 700;">Ticket Details</span>
                                    <hr>
                                </div>
                
                                <span style="font-size: 1.5rem;  text-align: center;">Status :</span>
                                <span style="font-weight: 700; font-size: 1.5rem;text-align: center;">{}</span>
                                <br>
                                <br>
                                <div style="display: flex; gap: 2px; margin-bottom: .5rem;">
                            <strong>Ticket raised by: </strong>
                                    <span>{}</span>
                                </div>
                                <div style="display: flex; gap: 2px; margin-bottom: .5rem;">
                            <strong>Ticket No: </strong>
                                    <span>{}</span>
                                </div>
                                <div style="display: flex; gap: 2px; margin-bottom: .5rem;">
                            <strong>Title: </strong>
                                    <span>{}</span>
                                </div>
                                <div style="display: flex; gap: 2px; margin-bottom: .5rem;">
                            <strong>Requirement Type: </strong>
                                    <span>{}</span>
                                </div>
                                <div style="display: flex; gap: 2px; margin-bottom: .5rem;">
                                    <strong>Approved By: </strong>
                                    <span>{}</span>
                                </div>
                                <div style="display: flex; gap: 2px; margin-bottom: .5rem;">
                                    <strong>Approved Status: </strong>
                                    <span>{}</span>
                                </div>
                                <div style="display: flex; gap: 2px; margin-bottom: .5rem;">
                                    <strong>Link: </strong>
                                    <a href="https://ador.net.in/login">ADORHUB</a>
                                </div>
                            </div>
                            <br>
                        <div style="display: flex;justify-content: center;">
                                <img src="https://adorwelding.org/Adorhub_uploads/Footer.png" width="700" alt="Conference Footer" style="display: flex;justify-content: center;">
                            </div>
                        </div>
                    </div>
                <br/>
                </body>
                </html>
                """.format(
            _data["current_approver_status"],
            _data["ticket_raised_by"],
            _data["ticket_no"],
            _data["title"],
            _data["requirement_type"],
            _data["current_approved_by"],
            _data["current_approver_comment"],
        )
        # Set up the email addresses and password. Please replace below with your email address and password
        email_from = from_email
        password = smtp_password
        # email_to = ["sharankudtarkar@adorians.com"]
        email_to = [
            _data["raised_by_mail_id"],
            _data["next_approver_mail_id"],
        ]

        # Create a MIMEMultipart class, and set up the From, To, Subject fields
        email_message = MIMEMultipart()
        email_message["From"] = email_from
        email_message["To"] = ", ".join(email_to)
        email_message["Subject"] = subject

        email_message.attach(MIMEText(html, "html"))
        email_string = email_message.as_string()

        with smtplib.SMTP("smtp-mail.outlook.com", 587) as server:
            server.starttls()
            server.login(email_from, password)
            server.sendmail(email_from, email_to, email_string)

        print("Email sent successfully")
        return Response("Email sent successfully", status=200)
    except Exception as e:
        print("Error in sending email:", e)
        return Response("Error in sending email", status=500)


def send_mail_early(instance):
    _data = {
        "raised_by_mail_id": user_details_from_emp_id(instance.requester_emp_no)[
            "email_id"
        ],
        "next_approver_mail_id": user_details_from_emp_id(instance.tkt_current_at)[
            "email_id"
        ],
        "ticket_raised_by": user_details_from_emp_id(instance.requester_emp_no)[
            "first_name"
        ]
        + " "
        + user_details_from_emp_id(instance.requester_emp_no)["last_name"],
        "ticket_no": instance.ticket_no,
        "title": instance.tkt_title,
        "requirement_type": instance.req_type,
        "ticket_link": instance.id,
    }

    try:
        load_dotenv()
        subject = "Adorhub - Ticket Notification"
        from_email = os.getenv("SENDER_EMAIL")
        smtp_server = os.getenv("SMTP_SERVER")
        smtp_port = os.getenv("SMTP_PORT")
        smtp_username = os.getenv("SMTP_USERNAME")
        smtp_password = os.getenv("SMTP_PASSWORD")
        tkt_link_prefix = os.getenv("TICKET_LINK_PREFIX")

        html = """
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <link href='https://fonts.googleapis.com/css?family=Source+Sans+Pro' rel='stylesheet' type='text/css'>
                    <meta charset="UTF-8">
                    <meta http-equiv="X-UA-Compatible" content="IE=edge">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                </head>
                <body style="padding: 1rem; font-family: 'Source Sans Pro', sans-serif;">
                    <div style="display: flex;">
                        <div style="width: 600px; margin-top: 1rem; display: grid; grid-template-columns: auto; gap: 2rem; width:fit-content;border-radius: 10px;padding:2rem;">
                            <img src="https://adorwelding.org/Adorhub_uploads/Ticket.png" width="800" alt="Conference Header" style="display: flex;justify-content: center;">
                            <div style="color: #555259; padding: 0 2rem;">
                                <div >
                                    <span style="font-size: 2rem; font-weight: 700;">Ticket Details</span>
                                    <hr>
                                </div>
                
                                <span style="font-size: 1.5rem;  text-align: center;">Status :</span>
                                <span style="font-weight: 700; font-size: 1.5rem;text-align: center;">RAISED</span>
                                <br>
                                <br>
                                <div style="display: flex; gap: 2px; margin-bottom: .5rem;">
                            <strong>Ticket raised by: </strong>
                                    <span>{}</span>
                                </div>
                                <div style="display: flex; gap: 2px; margin-bottom: .5rem;">
                            <strong>Ticket No: </strong>
                                    <span>{}</span>
                                </div>
                                <div style="display: flex; gap: 2px; margin-bottom: .5rem;">
                            <strong>Title: </strong>
                                    <span>{}</span>
                                </div>
                                <div style="display: flex; gap: 2px; margin-bottom: .5rem;">
                            <strong>Requirement Type: </strong>
                                    <span>{}</span>
                                </div>
                                <div style="display: flex; gap: 2px; margin-bottom: .5rem;">
                            <strong>Link: </strong>
                                    <a href="https://ador.net.in/login">ADORHUB</a>
                                </div>
                            </div>
                            <br>
                        <div style="display: flex;justify-content: center;">
                                <img src="https://adorwelding.org/Adorhub_uploads/Footer.png" width="700" alt="Conference Footer" style="display: flex;justify-content: center;">
                            </div>
                        </div>
                    </div>
                <br/>
                </body>
                </html>
        """.format(
            _data["ticket_raised_by"],
            _data["ticket_no"],
            _data["title"],
            _data["requirement_type"],
        )
        # Set up the email addresses and password. Please replace below with your email address and password
        email_from = from_email
        password = smtp_password
        # email_to = ["sharankudtarkar@adorians.com"]
        email_to = [
            _data["raised_by_mail_id"],
            _data["next_approver_mail_id"],
        ]

        # Create a MIMEMultipart class, and set up the From, To, Subject fields
        email_message = MIMEMultipart()
        email_message["From"] = email_from
        email_message["To"] = ", ".join(email_to)
        email_message["Subject"] = subject

        email_message.attach(MIMEText(html, "html"))
        email_string = email_message.as_string()

        with smtplib.SMTP("smtp-mail.outlook.com", 587) as server:
            server.starttls()
            server.login(email_from, password)
            server.sendmail(email_from, email_to, email_string)

        print("Email sent successfully")
        return Response("Email sent successfully", status=200)
    except Exception as e:
        print("Error in sending email:", e)
        return Response("Error in sending email", status=500)
