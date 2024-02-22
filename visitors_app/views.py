import pytz
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
from sanvad_project.settings import r
from io import BytesIO
import base64, binascii
import os
from django.core.files.base import ContentFile
from ticket_app.views import user_details_from_emp_id
from conference_app.views import user_info
from django.core.mail import send_mail
from django.shortcuts import render
import smtplib
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


# GET ALL DATA.
@api_view(["GET"])
def all_data(request):
    paginator = PageNumberPagination()
    search_query = request.GET["search"]
    woosee = "" if request.GET["woosee"] in security_det() else request.GET["woosee"]
    print(request.GET["date"])
    todays_date = (
        ""
        if request.GET["date"] == "false"
        else datetime.now().date().strftime("%Y-%m-%d")
    )
    print(todays_date)

    def _plant(emp_no):
        data = user_details_from_emp_id(emp_no)
        return (data["plant_name"].split(" ")[0]).upper()

    plant = (
        _plant(request.GET["woosee"]) if request.GET["woosee"] in security_det() else ""
    )

    paginator.page_size = 10
    base_sql_query = """SELECT
    vm.*,
    UPPER(um.plant_name) AS plant_name,
    CONCAT(um.first_name, ' ', um.last_name) AS name,
    um.department,
    TO_CHAR(vm.start_date_time::TIMESTAMP, 'DD-MM-YYYY hh:mi AM') AS mod_start_date_time,
    TO_CHAR(vm.end_date_time::TIMESTAMP, 'DD-MM-YYYY hh:mi AM') AS mod_end_date_time
FROM
    visitors_management vm
LEFT JOIN user_management um ON
    vm.raised_by = um.emp_no
WHERE
    vm.raised_by LIKE '%{}%'
    AND vm.delete_flag = false
    AND UPPER(plant_name) ILIKE '%{}%'
    AND (vm.reason_for_visit LIKE '%{}%' OR vm.raised_by LIKE '%{}%' OR vm.v_company LIKE '%{}%' OR vm.id::text LIKE '%{}%')
""".format(
        woosee,
        plant,
        search_query,
        search_query,
        search_query,
        search_query,
    )

    # Add time conditions based on the toggle
    if todays_date:
        time_conditions = "AND vm.start_date_time <= '{}'::TIMESTAMP AND vm.end_date_time >= '{}'::TIMESTAMP".format(
            todays_date + "T23:59:59",
            todays_date + "T00:00:00",
        )
        final_sql_query = base_sql_query + time_conditions
    else:
        final_sql_query = base_sql_query

    # Add the ORDER BY clause
    final_sql_query += " ORDER BY updated_at DESC;"

    with connection.cursor() as cursor:
        cursor.execute(final_sql_query)
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
        mail_confirmation(serializers.data)
        return Response({"mess": "Created", "status": status.HTTP_200_OK})

    else:
        print(serializers.errors)
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
    ##r = redis.Redis(host="localhost", port=6379, decode_responses=True)
    key_name = "security_admin"
    return r.lrange(key_name, 0, -1)


def mail_confirmation(data):
    try:
        user_details = user_info(data["raised_by"])
        _data = {
            "visitor_company": data["v_company"],
            "reason_for_vist": data["reason_for_visit"],
            "raised_by": str(user_details["first_name"]).title()
            + " "
            + str(user_details["last_name"]).title(),
            "department": user_details["department"],
            "start_date_time": datetime.strptime(
                data["start_date_time"], "%Y-%m-%dT%H:%M:%SZ"
            )
            .replace(tzinfo=pytz.timezone("UTC"))
            .astimezone(pytz.timezone("Asia/Kolkata"))
            .strftime("%d-%m-%Y %I:%M %p"),
            "end_date_time": datetime.strptime(
                data["end_date_time"], "%Y-%m-%dT%H:%M:%SZ"
            )
            .replace(tzinfo=pytz.timezone("UTC"))
            .astimezone(pytz.timezone("Asia/Kolkata"))
            .strftime("%d-%m-%Y %I:%M %p"),
            "main_visitors_name": data["visitors"][0]["v_name"],
            "visitor_count": len(data["visitors"]),
        }
        print(data)
        load_dotenv()
        subject = "Adorhub - Visitor Pass Details"
        from_email = os.getenv("SENDER_EMAIL")
        to_email = user_details["email_id"]
        smtp_server = os.getenv("SMTP_SERVER")
        smtp_port = os.getenv("SMTP_PORT")
        smtp_username = os.getenv("SMTP_USERNAME")
        smtp_password = os.getenv("SMTP_PASSWORD")

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

                    <span style="display: inline-block;">
                        Hi 
                        <span style="display: inline-block;">{}</span>,
                    </span>
                    <div style="display: flex;">
                        <div style="width: 600px; margin-top: 1rem; display: grid; grid-template-columns: auto; gap: 2rem; width:fit-content;border-radius: 10px;padding:2rem">
                        <br>
                            <img src="https://adorwelding.org/Adorhub_uploads/mail_vistor_header.png" width="800" alt="Conference Header" style="display: flex;justify-content: center;">
                            <br>
                            <div style="color: #555259; padding: 0 2rem;">
                                <div style="margin-bottom: 2rem;">
                                <br>
                                    <span style="font-size: 2rem; font-weight: 700;">Visitor Pass Details</span>
                                    <hr>
                                    <br>
                                </div>
                                <div style="display: flex; gap: 2px; margin-bottom: .5rem;">
                                    <span>Raised By: </span>
                                    <span>{}</span>
                                </div>

                                <div style="display: flex; gap: 2px; margin-bottom: .5rem;">
                                    <span>Department: </span>
                                    <span>{}</span>
                                </div>
                                <div style="display: flex; gap: 2px; margin-bottom: .5rem;">
                                    <span>Visitor Company: </span>
                                    <span>{}</span>
                                </div>
                                <div style="display: flex; gap: 2px; margin-bottom: .5rem;">
                                    <span>Main Visitor's Name: </span>
                                    <span>{}</span>
                                </div>
                                <div style="display: flex; gap: 2px; margin-bottom: .5rem;">
                                    <span>Reason For Vist: </span>
                                    <span>{}</span>
                                </div>
                                <div style="display: flex; gap: 2px; margin-bottom: .5rem;">
                                    <span>Start Date-time: </span>
                                    <span>{}</span>
                                </div>

                                <div style="display: flex; gap: 2px; margin-bottom: .5rem;">
                                    <span>End Date-Time: </span>
                                    <span>{}</span>
                                </div>
                                <div style="display: flex; gap: 2px; margin-bottom: .5rem;">
                                    <span>Total No of Visitors: </span>
                                    <span>{}</span>
                                </div>
                            </div>
                        <br>
                            <img src="https://adorwelding.org/Adorhub_uploads/Footer.png" width="700" alt="Conference Footer" style="display: flex;justify-content: center;">

                        </div>
                    </div>
                <br/>
                </body>
                </html> 
                        """.format(
            _data["raised_by"],
            _data["raised_by"],
            _data["department"],
            _data["visitor_company"],
            _data["main_visitors_name"],
            _data["reason_for_vist"],
            _data["start_date_time"],
            _data["end_date_time"],
            _data["visitor_count"],
        )

        # Set up the email addresses and password. Please replace below with your email address and password
        email_from = from_email
        password = smtp_password
        email_to = to_email

        # Create a MIMEMultipart class, and set up the From, To, Subject fields
        email_message = MIMEMultipart()
        email_message["From"] = email_from
        email_message["To"] = email_to
        email_message["Subject"] = "Adorhub - Visitor's Pass"

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
