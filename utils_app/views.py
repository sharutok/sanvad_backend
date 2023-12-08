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
from sanvad_project.settings import r
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
from sanvad_app.models import EmployeeMappings

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
    ##r = redis.Redis(host="localhost", port=6379, decode_responses=True)
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


@api_view(["GET"])
def serve_images(request):
    try:
        image_file = "http://localhost:8000/{}.png".format(request.data["image_name"])
        return Response({"status": status.HTTP_200_OK, "data": image_file})

    except Exception as e:
        print(e)
        return Response(
            {
                "status": status.HTTP_400_BAD_REQUEST,
            }
        )


@api_view(["GET"])
def plant_department_values(request):
    plant = "select * from "
    department = (
        "select distinct department  from employee_mappings em order by department asc;"
    )
    plant_name = (
        "select distinct plant_name  from employee_mappings em order by plant_name asc;"
    )

    _department_data = []
    department_data = select_sql(department)
    for x in department_data:
        _department_data.append(x["department"])

    _plant_name_data = []
    plant_name_data = select_sql(plant_name)
    for x in plant_name_data:
        _plant_name_data.append(x["plant_name"])

    return Response({"plant_data": _plant_name_data, "department": _department_data})


@api_view(["GET"])
def export_keys(output_file):
    try:
        output_file = "exported_keys.txt"
        with open(output_file, "w") as file:
            for key in r.scan_iter(match="*"):
                key_str = key.decode("utf-8") if isinstance(key, bytes) else key
                value = r.dump(key)
                file.write(f"{key_str}:{value.hex()}\n")
        return Response(200)
    except Exception as e:
        return Response(400)


@api_view(["GET"])
def import_keys():
    try:
        input_file = "exported_keys.txt"
        r = redis.Redis(
            host=os.environ.get("SERVER_REDIS_HOST"),
            port=os.environ.get("SERVER_REDIS_PORT"),
            password=os.environ.get("SERVER_REDIS_PASSWORD"),
        )

        r.flushall()
        with open(input_file, "r") as file:
            for line in file:
                parts = line.strip().split(":", 1)
                key_str = parts[0]
                value_hex = parts[1] if len(parts) > 1 else ""
                key = key_str.encode("utf-8")

                try:
                    value = bytes.fromhex(value_hex)
                except ValueError as e:
                    print(f"Error decoding hexadecimal value for key {key_str}: {e}")
                    continue
                r.restore(key, 0, value)
                return Response(200)
    except Exception as e:
        return Response(400)
