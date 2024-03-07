from django.db.models import Q
from rest_framework.response import Response
from rest_framework.decorators import api_view
from sanvad_app.models import UserManagement
from sanvad_app.serializers import userManagementSerializer
from rest_framework import status
import requests
from rest_framework.pagination import PageNumberPagination
from datetime import datetime,timedelta
from django.db import connection
import json
from sanvad_project.settings import r
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
import jwt

from utils_app.views import select_sql



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
    try:
        unsalted_password = str(request.data["password"]).encode("utf-8")
        salted_password = bcrypt.hashpw(unsalted_password, bcrypt.gensalt(rounds=10))
        request.data["password"] = salted_password.decode()
        serializers = userManagementSerializer(data=request.data)
        if serializers.is_valid():
            print("created")
            serializers.save()
        else:
            print("error", serializers.errors)
        return Response({"mess": "Created", "status": 200})
    except Exception as e:
        print("error", e)
        return Response(
            {
                "mess": "Not",
                "status": 400,
            }
        )


# VERIFY USER
@api_view(["POST"])
def login_verify_user(request):
    try:
        email = request.data["email"] + request.data["prefix"]
        password = request.data["password"]
        print(request.data)

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
                    is_feature = remember_me(serializers.data) if request.data['remember_me']==True else ""
                    return Response(
                        {
                            "status": status.HTTP_200_OK,
                            "emp_no": serializers.data["emp_no"],
                            "module_permission": serializers.data["module_permission"],
                            "initials": str(serializers.data["first_name"])[0:1]+ str(serializers.data["last_name"])[0:1],
                            "remember_me":str(is_feature),
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
        ##r = redis.Redis(host="localhost", port=6379, decode_responses=True)
        return Response({"data": json.loads(r.get("todays_birthday"))})
    except Exception as e:
        print("error", e)
        return Response({"error": e})


@api_view(["POST"])
def reset_password(request):
    try:
        emp_no = request.data["emp_no"]
        obj = UserManagement.objects.get(emp_no=emp_no)
        serializers = userManagementSerializer(obj)
        # check for
        user_status = serializers.data["user_status"]
        user_email = serializers.data["email_id"]
        first_name = serializers.data["first_name"][0:3].lower()
        dob = datetime.strptime(serializers.data["dob"], "%Y-%m-%d")
        DD = dob.strftime("%d")
        MM = dob.strftime("%m")
        if user_email and emp_no and obj:
            collection = hash_password(first_name + DD + MM)
            password = collection[1]
            actual_password = collection[0]
            serializers = userManagementSerializer(
                obj, data={"password": password.decode("utf-8")}
            )
            if serializers.is_valid():
                serializers.save()

            load_dotenv()
            subject = "ADOR HUB - Oops! Forgot Your Password? No Worries, We Gave It a Makeover"
            from_email = os.getenv("SENDER_EMAIL")
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
                            <body style="padding: 1rem;font-family: 'Source Sans Pro', sans-serif;">
                                <span >Hi <span > {} </span>,</span>
                                <div style="margin-top: 1rem; display: grid; grid-template-columns: auto;gap: 5px; ">
                                    <span>Your Password for ADOR HUB Application has been reset successfully.</span>
                                    <p>Password : <strong> {} </strong></p>
                                        <p>Use the link to Log in <a href="https://ador.net.in">ADOR HUB</a></p>
                                        
                                    </div>
                                    <p>Thanks & Regards.. </p>
                                    <img src="https://upload.wikimedia.org/wikipedia/commons/9/98/Ador_Welding_logo.png" alt="Ador Logo" width="100"
                                    height="50">
                                    <br />
                                    <br />
                            </body>
                            </html>
            """.format(
                obj, actual_password
            )
            email_from = from_email
            password = smtp_password
            email_to = user_email
            # Create the email message
            email_message = MIMEMultipart()
            email_message["From"] = email_from
            email_message["To"] = email_to
            email_message["Subject"] = subject

            email_message.attach(MIMEText(html, "html"))
            email_string = email_message.as_string()

            with smtplib.SMTP("smtp-mail.outlook.com", 587) as server:
                server.starttls()
                server.login(email_from, password)
                server.sendmail(email_from, email_to, email_string)

            print("Email sent successfully")
            return Response({"status_code": status.HTTP_200_OK})

    except Exception as e:
        print(e)
        return Response({"status_code": status.HTTP_400_BAD_REQUEST})


def hash_password(ran):
    print(ran)
    unsalted_password = str(ran).encode("utf-8")
    salted_password = bcrypt.hashpw(unsalted_password, bcrypt.gensalt(rounds=10))
    print(ran, unsalted_password, salted_password)
    return [ran, salted_password]


# DYNAMIC VALUES- user_permission
@api_view(["POST", "GET", "DELETE"])
def user_permission_dynamic_values(request):
    ##r = redis.Redis(host="localhost", port=6379, decode_responses=True)
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


@api_view(["GET"])
def get_list_of_managers_based_on_department(request):
    department = request.GET["department"]
    query = """select concat(first_name,' ',last_name) name from user_management um where um.user_status =true"""
    with connection.cursor() as cursor:
        cursor.execute(query)
        results = cursor.fetchall()
        rows = [
            dict(zip([col[0] for col in cursor.description], row)) for row in results
        ]
    return Response(rows)

def remember_me(obj):
    try:
        secret_key = '!kp_s,zn2ir0wiascn[oquoq]'
        _emp_no=obj['emp_no']
        hashed_random_string = {
        'user_id': _emp_no,
        'exp': datetime.utcnow() + timedelta(days=7),  # Expiry 7 days from now
        "emp_no":obj['emp_no'],
        "module_permission":obj['module_permission'],
        "initials":str(obj["first_name"])[0:1]+ str(obj["last_name"])[0:1],
        }

        # Generate JWT token
        token = jwt.encode(hashed_random_string, secret_key, algorithm='HS256')
        sql='''update user_management set remember_me_auth ='{}' where emp_no ='{}';'''.format(token,_emp_no)
        cursor = connection.cursor()
        cursor.execute(sql)
        return token
    except Exception as e:
        print("error in remember_me",e)

@api_view(["GET"])
def validate_remember_me(request):
    secret_key = '!kp_s,zn2ir0wiascn[oquoq]'
    token =  request.GET["token"]
    try:
        data=jwt.decode(token, secret_key, algorithms=['HS256'])
        select_sql("SELECT * FROM user_management um where manager_code ='15604'".format())
        print("valid")
        return Response({"mess":200,"data":data})
    except jwt.ExpiredSignatureError:
        print("JWT token has expired.")
        return Response({"mess":400})
    except jwt.InvalidTokenError:
        print("Invalid JWT token.")
        return Response({"mess":400})