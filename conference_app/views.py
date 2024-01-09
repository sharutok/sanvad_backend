import base64
from django.core.mail import send_mail
from django.shortcuts import render
import smtplib
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.db import connection
from django.db.models import Q
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.shortcuts import render
from conference_app.models import ConferenceBooking
from conference_app.serializers import ConferenceBookingSerializer
from ticket_app.views import user_details_from_emp_id
from sanvad_app.serializers import userManagementSerializer
from sanvad_app.models import UserManagement
from rest_framework import status
import requests
from datetime import datetime, timedelta
from sanvad_project.settings import r
from rest_framework.pagination import PageNumberPagination
import os
from email.message import EmailMessage
from capex_app.views import execute_sql


# GET ALL DATA.
@api_view(["GET"])
def all_data(request):
    paginator = PageNumberPagination()
    search_query = request.GET["search"]
    woosee = request.GET["woosee"]

    todays_date = request.GET["date"]
    todays_date = (
        ""
        if request.GET["date"] == "false"
        else datetime.now().date().strftime("%Y-%m-%d")
    )
    results = all_conference_rooms(woosee, "conference_rooms")

    arr = []
    for result in results:
        arr.append(result.split("#")[0])
    print(arr)

    raw_sql_query = """
                    select
                    	cb.*,
	                    um.first_name ,
	                    um.last_name ,
	                    um.department
                    from
                    	conference_booking cb,user_management um
                    where
                    1=1 
                    and cb.conf_by = um.emp_no 
                    and cb.delete_flag = false 
                    and cb.conf_room in {}
                    and (conf_room LIKE '%{}%'
                        OR conf_by LIKE '%{}%'
                        OR meeting_about LIKE '%{}%') AND conf_end_date::text LIKE '%{}%' order by cb.created_at desc ;""".format(
        tuple(arr), search_query, search_query, search_query, todays_date
    )
    with connection.cursor() as cursor:
        cursor.execute(raw_sql_query)
        results = cursor.fetchall()
        rows = [
            dict(zip([col[0] for col in cursor.description], row)) for row in results
        ]
    paginator.page_size = 10
    result_page = paginator.paginate_queryset(rows, request)
    return paginator.get_paginated_response(result_page)


# GET & DELETE BY ID
@api_view(["GET", "DELETE"])
def data_by_id(request, id):
    match request.method:
        case "GET":
            obj = ConferenceBooking.objects.get(pk=id)
            serializers = ConferenceBookingSerializer(obj)
            return Response(
                {"data": serializers.data, "status_code": status.HTTP_200_OK}
            )
        case "DELETE":
            try:
                ConferenceBooking.objects.filter(id=id).update(delete_flag=True)
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

            # obj = ConferenceBooking.objects.get(pk=id)
            # request.data["delete_flag"] = "Y"
            # serializers = ConferenceBookingSerializer(obj, data=request.data)
            # if serializers.is_valid():
            #     serializers.save()
            #     return Response(
            #         {"data": serializers.data, "status_code": status.HTTP_200_OK}
            #     )
            # return Response(
            #     {
            #         "error": serializers.errors,
            #         "status_code": status.HTTP_400_BAD_REQUEST,
            #     }
            # )


# CREATE
@api_view(["POST"])
def create(request):
    try:
        start_date_time = request.data["start_date_time"]
        end_date_time = request.data["end_date_time"]

        start_date_time_object = datetime.strptime(start_date_time, "%Y-%m-%d %I:%M %p")
        end_date_time_object = datetime.strptime(end_date_time, "%Y-%m-%d %I:%M %p")

        start_date_component = start_date_time_object.date()
        start_time_component = start_date_time_object.time()

        end_date_component = end_date_time_object.date()
        end_time_component = end_date_time_object.time()

        data = {
            "conf_by": request.data["conf_by"],
            "meeting_about": request.data["meeting_about"],
            "conf_start_date": start_date_component,
            "conf_start_time": start_time_component,
            "conf_end_date": end_date_component,
            "conf_end_time": end_time_component,
            "conf_room": request.data["conf_room"],
            "disp_conf_end_date": "",
        }

        date1 = datetime.strptime(str(data["conf_end_date"]), "%Y-%m-%d")
        date2 = datetime.strptime(str(data["conf_start_date"]), "%Y-%m-%d")

        data["disp_conf_end_date"] = datetime.strptime(
            str(data["conf_end_date"]), "%Y-%m-%d"
        ).date()
        # CALCULATE THE DIFFERENCE BETWEEN THE TWO DATES
        delta = date1 - date2

        # GET THE NUMBER OF DAYS AS AN INTEGER
        num_days = delta.days
        end_dates = []
        if num_days >= 0:
            for _date in range(num_days + 1):
                result_date = date2 + timedelta(days=_date)
                end_dates.append(str(result_date).split(" ")[0])

        for date in end_dates:
            data["conf_end_date"] = datetime.strptime(date, "%Y-%m-%d").date()
            serializers = ConferenceBookingSerializer(data=data)
            if serializers.is_valid():
                serializers.save()
        # mail_confirmation(serializers.data)
        return Response({"mess": "Created", "status": 200})
    except Exception as e:
        return Response({"mess": "Not", "status": 400, "err": e})


# GET BY CONF ROOM & DATE
@api_view(["POST"])
def get_data_by_cof_room_and_date(request):
    try:
        conf_room = request.data.get("conf_room")
        conf_end_date = request.data.get("conf_end_date")
        print(conf_room, conf_end_date)

        if True:
            # if conf_room and conf_end_date and delete_flag:
            # queryset = ConferenceBooking.objects.filter(
            #     conf_room=conf_room,
            #     conf_end_date=conf_end_date,
            #     delete_flag=delete_flag,
            # )
            raw_sql_query = """
                                select
                            	cb.*,
                            	                    um.first_name ,
                            	                    um.last_name ,
                            	                    um.department
                            from
                            	conference_booking cb,
                            	user_management um
                            where
                            	1 = 1
                            	and cb.conf_by = um.emp_no
                            	and conf_room = '{}'
                            	and delete_flag = 'N'
                            and conf_end_date::text ='{}'
                            ;""".format(
                conf_room, conf_end_date
            )
            with connection.cursor() as cursor:
                cursor.execute(raw_sql_query)
                results = cursor.fetchall()
                rows = [
                    dict(zip([col[0] for col in cursor.description], row))
                    for row in results
                ]
            return Response({"data": rows, "status_code": status.HTTP_200_OK})
        else:
            return Response(
                {
                    "data": "Missing parameters",
                    "status_code": status.HTTP_400_BAD_REQUEST,
                }
            )
    except Exception as e:
        return Response(
            {"data": str(e), "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR}
        )


@api_view(["GET", "PUT", "DELETE"])
def conference_rooms_dynamic_values(request):
    ##r = redis.Redis(host="localhost", port=6379, decode_responses=True)
    key_name = "conference_rooms"
    match request.method:
        # GET ALL DATA
        case "GET":
            try:
                woosee = request.GET["woosee"]
                result = all_conference_rooms(woosee, key_name)
                return Response(result)

            except Exception as e:
                print(e)
                return Response(False)
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


def mail_confirmation(data):
    try:
        user_details = user_info(data["conf_by"])

        _data = {
            "book_who": str(user_details["first_name"]).title()
            + " "
            + str(user_details["last_name"]).title(),
            "meeting_about": str(data["meeting_about"]).title(),
            "location": data["conf_room"],
            "start_data_time": data["conf_start_date"] + " " + data["conf_start_time"],
            "end_data_time": data["conf_end_date"] + " " + data["conf_end_time"],
            "dept": user_details["department"],
        }

        load_dotenv()
        subject = "Adorhub - Conference Booked"
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
            <img src="https://adorwelding.org/Adorhub_uploads/Conference.png" width="800" alt="Conference Header" style="display: flex;justify-content: center;">
            <br>
            <div style="color: #555259; padding: 0 2rem;">
                <div style="margin-bottom: 2rem;">
                <br>
                    <span style="font-size: 2rem; font-weight: 700;">Conference Details</span>
                    <hr>
                    <br>
                </div>

                <div style="display: flex; gap: 2px; margin-bottom: .5rem;">
                    <span>Agenda: </span>
                    <span>{}</span>
                </div>

                <div style="display: flex; gap: 2px; margin-bottom: .5rem;">
                    <span>Location: </span>
                    <span>{}</span>
                </div>

                <div style="display: flex; gap: 2px; margin-bottom: .5rem;">
                    <span>Start Date/Time: </span>
                    <span>{}</span>
                </div>

                <div style="display: flex; gap: 2px; margin-bottom: .5rem;">
                    <span>End Date/Time: </span>
                    <span>{}</span>
                </div>

                <div style="display: flex; gap: 2px; margin-bottom: .5rem;">
                    <span>Booked By: </span>
                    <span>{}</span>
                </div>

                <div style="display: flex; gap: 2px; margin-bottom: .5rem;">
                    <span>Department:</span>
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
            _data["book_who"],
            _data["meeting_about"],
            _data["location"],
            _data["start_data_time"],
            _data["end_data_time"],
            _data["book_who"],
            _data["dept"],
        )

        # Set up the email addresses and password. Please replace below with your email address and password
        email_from = from_email
        password = smtp_password
        email_to = to_email

        # Create a MIMEMultipart class, and set up the From, To, Subject fields
        email_message = MIMEMultipart()
        email_message["From"] = email_from
        email_message["To"] = email_to
        email_message["Subject"] = "Adorhub - Conference Booking Confirmation"

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


def user_info(emp_no):
    obj = UserManagement.objects.get(emp_no=emp_no)
    serializers = userManagementSerializer(obj)
    return serializers.data


def all_conference_rooms(woosee, key_name):
    plant_name = user_details_from_emp_id(woosee)["plant_name"]
    val = execute_sql(
        "select UPPER(split_part(plant_name,' ',1))plant_name from user_management um where emp_no ='{}'".format(
            woosee
        )
    )
    data = r.lrange(key_name, 0, -1)
    if val[0]["plant_name"]:
        _data = []
        for room in data:
            if room.split("#")[2] == val[0]["plant_name"]:
                _data.append(room)
        _data = _data if len(_data) else data
        return _data
