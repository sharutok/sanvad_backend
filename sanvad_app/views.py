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
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os
import random
import string
import PIL.Image as Image
import io
import base64


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
            | Q(plant_name__icontains=search_query)
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
            try:
                obj = UserManagement.objects.get(pk=id)
                serializers = userManagementSerializer(obj, data=request.data)
                if serializers.is_valid():
                    serializers.save()
                else:
                    print(serializers.errors)
                return Response(
                    {"data": serializers.data, "status_code": status.HTTP_200_OK}
                )
            except Exception as e:
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
    unsalted_password = str(serializers.data["password"]).encode("utf-8")
    salted_password = bcrypt.hashpw(unsalted_password, bcrypt.gensalt(rounds=10))
    serializers.data["password"] = salted_password
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
            obj = UserManagement.objects.get(email_id=email)
            serializers = userManagementSerializer(obj)
            if queryset_email.exists() and (serializers.data["user_status"] == True):
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
                    return Response({"status": status.HTTP_400_BAD_REQUEST})
            else:
                return Response({"status": status.HTTP_400_BAD_REQUEST})
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


@api_view(["POST"])
def reset_password(request):
    try:
        if request.data["user_email"] and request.data["emp_no"]:
            user_email = request.data["user_email"]
            emp_no = request.data["emp_no"]
            collection = hash_password()
            password = collection[1]
            actual_password = collection[0]
            obj = UserManagement.objects.get(emp_no=emp_no)
            serializers = userManagementSerializer(
                obj, data={"password": password.decode("utf-8")}
            )
            if serializers.is_valid():
                serializers.save()

            load_dotenv()
            smtp_server = os.getenv("SMTP_SERVER")
            smtp_port = os.getenv("SMTP_PORT")
            smtp_username = os.getenv("SMTP_USERNAME")
            smtp_password = os.getenv("SMTP_PASSWORD")
            sender_email = os.getenv("SENDER_EMAIL")
            receiver_email = user_email
            subject = "ADOR HUB Password Reset"

            html_message = """
                        <!DOCTYPE html>
                            <html lang="en">
                            <head>
                                <link href='https://fonts.googleapis.com/css?family=Source+Sans+Pro' rel='stylesheet' type='text/css'>
                                <meta charset="UTF-8">
                                <meta http-equiv="X-UA-Compatible" content="IE=edge">
                                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                            </head>
                            <body style="padding: 1rem;font-family: 'Source Sans Pro', sans-serif;">
                                <span >Hi <span > {} !</span>,</span>
                                <div style="margin-top: 1rem; display: grid; grid-template-columns: auto;gap: 5px; ">
                                    <span>Your Password for ADOR HUB Application has been reset successfully.</span>
                                    <p>Password : <strong> {} </strong></p>
                                        <p>Use the link below to Log in.</p>
                                        <p>
                                            <a href="www.google.com">ADOR HUB</a>
                                        </p>
                                    </div>
                                    <br />
                                    <p>Thanks & Regards.. </p>
                                    <img src="https://upload.wikimedia.org/wikipedia/commons/9/98/Ador_Welding_logo.png" alt="Ador Logo" width="100"
                                    height="50">
                                    <br />
                                    <br />
                                    <h4 style="font-weight: bolder;align-items: center;font-style: italic;"> -: This is a system-generated :- </h4>
                            </body>
                            </html>
            """.format(
                obj, actual_password
            )
            # Create the email message
            msg = MIMEMultipart()
            msg["From"] = sender_email
            msg["To"] = receiver_email
            msg["Subject"] = subject
            msg.attach(
                MIMEText(
                    html_message,
                    "html",
                )
            )
            # Establish a connection to the SMTP server

            server = smtplib.SMTP(smtp_server, smtp_port)
            server.login(smtp_username, smtp_password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
            print("Email sent successfully.")
            server.quit()
            return Response({"status_code": status.HTTP_200_OK})
    except Exception as e:
        print(e)
        return Response({"status_code": status.HTTP_400_BAD_REQUEST})


def random_password():
    special_characters = ["!", "@", "#", "$", "%"]
    lowercase_letters = list(string.ascii_lowercase)

    v1 = random.choice(special_characters)
    v2 = random.choice(lowercase_letters)
    v3 = random.choice(lowercase_letters)
    v4 = random.choice(lowercase_letters)
    v5 = random.choice(special_characters)

    return v1 + v2 + v3 + v4 + v5


def hash_password():
    ran = random_password()
    unsalted_password = str(ran).encode("utf-8")
    salted_password = bcrypt.hashpw(unsalted_password, bcrypt.gensalt(rounds=10))
    print(ran, unsalted_password, salted_password)
    return [ran, salted_password]


# DYNAMIC VALUES- user_permission
@api_view(["POST", "GET", "DELETE"])
def user_permission_dynamic_values(request):
    r = redis.Redis(host="localhost", port=6379, decode_responses=True)
    key_name = "user_permission"
    match request.method:
        # ALL DATA
        case "GET":
            data = r.lrange(key_name, 0, -1)
            data = sorted(data, key=lambda x: (x.split(":")[0]))
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
