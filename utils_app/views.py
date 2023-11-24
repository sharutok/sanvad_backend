from django.db import connection
from django.shortcuts import render
import pandas
from rest_framework import status
import json
from rest_framework.response import Response
from rest_framework.decorators import api_view
import mimetypes
from django.http import HttpResponse
from wsgiref.util import FileWrapper
import redis
from django.http import FileResponse
from django.conf import settings
import os
from django.db.models import F
import datetime
from utils_app.serializers import AnnounsmentSerializer

from utils_app.models import Announsment
from sanvad_app.models import UserManagement
from ticket_app.models import TicketSystemModel
from conference_app.models import ConferenceBooking
from visitors_app.models import VisitorsManagement
from capex_app.models import Capex, Capex1

# Create your views here.


@api_view(["POST"])
def download_excel(request):
    try:
        data_module = request.data["data_module"]
        data = ""
        match data_module:
            case "user_manage":
                data = (
                    UserManagement.objects.filter(user_status=True)
                    .order_by("-updated_at")
                    .annotate(
                        EMP_NO=F("emp_no"),
                        FIRST_NAME=F("first_name"),
                        LAST_NAME=F("last_name"),
                        DEPARTMENT=F("department"),
                        PLANT_NAME=F("plant_name"),
                        ORGANIZATION=F("organization"),
                        USER_STATUS=F("user_status"),
                        START_DATE=F("start_date"),
                    )
                    .values(
                        "EMP_NO",
                        "FIRST_NAME",
                        "LAST_NAME",
                        "DEPARTMENT",
                        "PLANT_NAME",
                        "ORGANIZATION",
                        "USER_STATUS",
                        "START_DATE",
                    )[:100]
                )
            case "ticket":
                data = (
                    TicketSystemModel.objects.filter(delete_flag=False)
                    .order_by("-updated_at")
                    .annotate(
                        TICKET_NO=F("ticket_no"),
                        TKT_TITLE=F("tkt_title"),
                        TKT_TYPE=F("tkt_type"),
                        REQ_TYPE=F("req_type"),
                        REQUESTER_EMP_NO=F("requester_emp_no"),
                        SEVERITY=F("severity"),
                        CREATED_AT=F("created_at"),
                        TKT_STATUS=F("tkt_status"),
                        TKT_CURRENT_AT=F("tkt_current_at"),
                    )
                    .values(
                        "TICKET_NO",
                        "TKT_TITLE",
                        "TKT_TYPE",
                        "REQ_TYPE",
                        "REQUESTER_EMP_NO",
                        "SEVERITY",
                        "CREATED_AT",
                        "TKT_STATUS",
                        "TKT_CURRENT_AT",
                    )[:100]
                )
            case "conference":
                raw_sql = """
                select
                    	cb.meeting_about  "Meeting title",
                    	cb.conf_start_date "Meeting Date",
                    	cb.conf_start_time "Start Time",
                    	cb.conf_end_time  "End Time",
                    	cb.conf_room "Conference",
	                    concat (um.first_name,' ' ,um.last_name) "Booked By" ,
	                    um.department "Department"
                    from
                    	conference_booking cb,user_management um
                    where
                    1=1 and
                    	cb.conf_by = um.emp_no and
                    cb.delete_flag = false order by cb.created_at desc limit 100;
                """
                data = select_sql(raw_sql)
            case "visitor":
                raw_sql = """
                    select
                    	reason_for_visit "Visitor's Reason For Vist",
                    	concat(um.first_name,
                    	' ',
                    	um.last_name) "Raised By",
                    	um.department "Department" ,
                    	to_char(vm.start_date_time ::timestamp ,
                    	'DD-MM-YYYY hh:mi AM') "Start Date-time" ,
                    	to_char(vm.end_date_time ::timestamp ,
                    	'DD-MM-YYYY hh:mi AM') "End Date-Time",
                    	jsonb_array_length(visitors) "Visitor Count"
                    from
                    	visitors_management vm
                    left join user_management um on
                    	vm.raised_by = um.emp_no where vm.delete_flag  = false order by vm.updated_at desc limit 100;
                """
                data = select_sql(raw_sql)
            case "capex":
                raw_sql = """ 
                    select
	                        cem.budget_no "Budget No",
                        	cem.line_no "Line No",
                        	cem.purpose_code "Purpose code",
                        	cdm.requisition_date "Requisition Date",
                        	cdm.payback_period "Payback Period",
                        	cdm.return_on_investment "Return On Investment",
                        	cdm.budget_type "Budget Type",
                        	concat(um.first_name,
                        	' ',
                        	um.last_name) "Current At",
                        	cdm.capex_status "Capex Status"
                        from
                        	capex_data_master cdm
                        left join user_management um on
                        	cdm.capex_current_at = um.emp_no
                        left join capex_excel_master cem on
                        	cem.id = cdm.budget_id
                        where
                        	cdm.delete_flag = false
                        order by
                        	cdm.updated_at desc
                        limit 100;"""
                data = select_sql(raw_sql)
        return Response({"status_code": status.HTTP_200_OK, "data": data})
    except Exception as e:
        print(e)
        return Response({"status_code": status.HTTP_400_BAD_REQUEST})


@api_view(["GET"])
def weather_temp(request):
    r = redis.Redis(host="localhost", port=6379, decode_responses=True)
    return Response({"data": json.loads(r.get("weather_temp"))})


@api_view(["GET"])
def serve_files(request):
    file_path = os.path.join(
        settings.MEDIA_ROOT,
        "ticket/f41e98af-483d-4b2b-b118-cabc8c5b821b/Distributor_application_16-Oct-2023.pdf",
    )
    print(settings.MEDIA_ROOT)
    # Check if the file exists
    if os.path.exists(file_path):
        with open(file_path, "rb") as pdf_file:
            response = FileResponse(pdf_file, as_attachment=True)
            return response
    else:
        # Handle the case where the file does not exist
        print("File not found")
        return HttpResponse("File not found", status=404)


def select_sql(raw_sql_query):
    with connection.cursor() as cursor:
        cursor.execute(raw_sql_query)
        results = cursor.fetchall()
        rows = [
            dict(zip([col[0] for col in cursor.description], row)) for row in results
        ]
    return rows


@api_view(["POST", "GET", "DELETE"])
def announcement(request):
    match request.method:
        case "POST":
            try:
                serializers = AnnounsmentSerializer(data=request.data)
                if serializers.is_valid():
                    serializers.save()
                return Response({"status": status.HTTP_200_OK})
            except:
                return Response(
                    {
                        "status": status.HTTP_400_BAD_REQUEST,
                    }
                )
        case "GET":
            try:
                current_date = datetime.datetime.now().strftime("%d-%m-%Y")
                print(current_date)
                raw_sql_query = """
                                    select * from (SELECT *,
                                    to_date(to_char(created_at + interval '7' day, 'DD-MM-YYYY'), 'DD-MM-YYYY') as expiry_date
                                    FROM announsments) tbl where to_date('{}', 'DD-MM-YYYY') <= tbl.expiry_date ;
                """.format(
                    current_date
                )
                with connection.cursor() as cursor:
                    cursor.execute(raw_sql_query)
                    results = cursor.fetchall()
                    rows = [
                        dict(zip([col[0] for col in cursor.description], row))
                        for row in results
                    ]
                return Response({"status": status.HTTP_200_OK, "data": rows})
            except Exception as e:
                print(e)
                return Response(
                    {
                        "status": status.HTTP_400_BAD_REQUEST,
                    }
                )
        case "DELETE":
            try:
                serializers = AnnounsmentSerializer(data=request.data)
                if serializers.is_valid():
                    serializers.save()
                return Response({"status": status.HTTP_200_OK})
            except:
                return Response(
                    {
                        "status": status.HTTP_400_BAD_REQUEST,
                    }
                )
