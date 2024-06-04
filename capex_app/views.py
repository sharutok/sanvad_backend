import pdfkit
import json
from rest_framework.response import Response
from rest_framework.decorators import api_view
from capex_app.models import Capex, Capex1
from rest_framework.pagination import PageNumberPagination
from capex_app.serializers import (
    CapexSerializer,
    Capex1Serializer,
    UploadBudgetSerializer,
)
import smtplib
from copy import deepcopy
from rest_framework import status
import pandas as pd
import requests
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sanvad_project.settings import r
import os
from utils_app.views import common_mail_template
from django.db import connection
from ticket_app.views import user_details_from_emp_id
from datetime import datetime
from psycopg2.extras import Json
from sanvad_app.models import UserManagement
from sanvad_app.serializers import userManagementSerializer
from django.http import HttpResponse


# READ EXCEL DATA AND PUSH
@api_view(["POST"])
def read_data_excel(request):
    try:
        serializers = UploadBudgetSerializer(data=request.data)
        obj = ""
        if serializers.is_valid():
            print("file saved")
            obj = serializers.save()
        else:
            print(serializers.errors)

        current_directory = os.path.dirname(os.path.abspath(__file__))
        excel_file_path = os.path.join(
            current_directory, "../media", str(obj.budget_file)
        )
        print(excel_file_path)

        df = pd.read_excel(excel_file_path)
        json_data = df.to_dict(orient="records")

        for row in json_data:
            serializers = CapexSerializer(
                data={
                    "budget_no": row["BUDGET NO"],
                    "purpose_code": row["PURPOSE CODE"],
                    "purpose_description": row["PURPOSE"],
                    "line_no": row["LINE NO"],
                    "plant": row["LOCATION"],
                    "dept": row["DEPARTMENT"],
                    "capex_group": row["CAPEX GROUP"],
                    "capex_class": row["CLASS"],
                    "category": row["CATEGORY"],
                    "asset_description": row["ASSET DESCRIPTION"],
                    "details": row["DETAILS"],
                    "rate": row["RATE"],
                    "qty": row["QTY"],
                    "uom": row["UOM"],
                    "final_budget": row["FINAL BUDGET"],
                    "remarks": row["REMARKS"],
                }
            )
            if serializers.is_valid():
                serializers.save()
            print(serializers.errors)
        return Response({"mess": "Created", "status": 200})

    except Exception as e:
        print(e)
        return Response({"errors": e})


# GET ALL BUDGET DATA
@api_view(["GET"])
def get_all_budget_data(request):
    search_query = request.GET["search"]
    woosee = request.GET["woosee"]

    user_info = UserManagement.objects.get(emp_no=woosee)
    user_info = userManagementSerializer(user_info)

    plant_name = "" if woosee in get_capex_admin() else user_info.data["plant_name"]
    department = "" if woosee in get_capex_admin() else user_info.data["department"]

    raw_sql_query = """
                            select
                            	*
                            from
                            	capex_excel_master cem,
                            	(
                            	SELECT
                                cem.id AS budget_id,
                                COALESCE(COUNT(cdm.budget_id), 0) AS no_of_capex,
                                ROUND(COALESCE(SUM(cdm.total_cost),0)::numeric ,2) AS consumed,
                                ROUND(COALESCE(cem.final_budget/100000,0)::numeric,2) AS final_budget,
                                ROUND(COALESCE(COALESCE(cem.final_budget/100000,0) - COALESCE(SUM(cdm.total_cost),0),0)::numeric ,2) AS budget_remaining
                            FROM
                                capex_excel_master cem
                            LEFT JOIN
                                capex_data_master cdm
                            ON
                                cem.id = cdm.budget_id
                            GROUP BY
                                cem.id, cem.final_budget) t1
                            where
                            	t1.budget_id = cem.id
                                and cem.plant ilike '%{}%' and cem.dept ilike '%{}%'
                                and cem.delete_flag=false
                                and (
                                    cem.budget_no ilike '%{}%' 
                                or cem.purpose_code ilike '%{}%' 
                                or cem.purpose_description ilike '%{}%' 
                                or category ilike '%{}%' 
                                or plant ilike '%{}%' 
                                or dept ilike '%{}%' 
                                or capex_group ilike '%{}%' 
                                or asset_description ilike '%{}%')
                                order by created_at desc;""".format(
        plant_name,
        department,
        search_query,
        search_query,
        search_query,
        search_query,
        search_query,
        search_query,
        search_query,
        search_query,
    )
    with connection.cursor() as cursor:
        cursor.execute(raw_sql_query)
        results = cursor.fetchall()
        rows = [
            dict(zip([col[0] for col in cursor.description], row)) for row in results
        ]
    paginator = PageNumberPagination()
    paginator.page_size = 10
    result_page = paginator.paginate_queryset(rows, request)
    return paginator.get_paginated_response(result_page)


# GET ALL CAPEX DATA
@api_view(["GET"])
def get_all_capex_data(request):
    try:
        search_query = request.GET["search"]
        user_details = user_details_from_emp_id(request.GET["woosee"])
        department = ""
        woosee = ""
        view = request.GET["view"]
        raw_sql_query = ""

        # PERMISSION ACCORDING TO VIEW
        match view:
            # CAPEX DATA
            case "approve_capex_view":
                woosee = request.GET["woosee"]
                department = ""
                raw_sql_query = """select
                            cdm.id capex_no,
                            cem.budget_no ,
                            cdm.nature_of_requirement ,
                            cdm.total_cost,
                            cem.purpose_code ,
                            to_char(cdm.requisition_date::timestamp, 'DD-MM-YYYY') requisition_date,
                            cdm.payback_period ,
                            cdm.return_on_investment ,
                            um1.department,
                            cdm.budget_type,
                            cdm.budget_id ,
                            cdm.id capex_id,
                            to_char(cdm.created_at::timestamp, 'DD-MM-YYYY') created_at,
                            concat(um.first_name,' ',um.last_name) capex_current_at,
                            concat(um1.first_name,' ',um1.last_name) capex_raised_by,
                            cdm.capex_status
                            from
                                capex_data_master cdm
                            left join user_management um on
                                cdm.capex_current_at = um.emp_no
                            left join capex_excel_master cem on
                            cem.id = cdm.budget_id 
                            left join user_management um1 on
                            cdm.capex_raised_by =um1.emp_no 
                            where 
                            cdm.delete_flag=false and ((cdm.capex_raised_by like '%{}%' or cdm.capex_current_at like '%{}%') and 
                            (
                                cdm.id::text ilike '%{}%'
                                or cem.budget_no ilike '%{}%' 
                                or cem.purpose_code ilike '%{}%' 
                                or cdm.return_on_investment ilike '%{}%'
                                )) order by cdm.created_at desc ;""".format(
                    woosee,
                    woosee,
                    search_query,
                    search_query,
                    search_query,
                    search_query,
                    search_query,
                )
            # RESPECTIVE DEPARTMENT CAPEX
            case "dept_capex_view":
                department = user_details["department"]
                plant_name = user_details["plant_name"]
                raw_sql_query = """ 
                            select
                            cdm.id capex_no,
                            cem.budget_no ,
                            cdm.nature_of_requirement ,
                            cdm.total_cost,
                            cem.purpose_code ,
                            to_char(cdm.requisition_date::timestamp, 'DD-MM-YYYY') requisition_date,
                            cdm.payback_period ,
                            cdm.return_on_investment ,
                            um1.department,
                            cdm.budget_type,
                            cdm.budget_id ,
                            cdm.id capex_id,
                            to_char(cdm.created_at::timestamp, 'DD-MM-YYYY') created_at,
                            concat(um.first_name,' ',um.last_name) capex_current_at,
                            concat(um1.first_name,' ',um1.last_name) capex_raised_by,
                            cdm.capex_status
                            from
                                capex_data_master cdm
                            left join user_management um on
                                cdm.capex_current_at = um.emp_no
                            left join capex_excel_master cem on
                            cem.id = cdm.budget_id 
                            left join user_management um1 on
                            cdm.capex_raised_by =um1.emp_no 
                            where 
                            cdm.delete_flag=false and um1.department like '%{}%' and um1.plant_name like '%{}%'  and 
                            (
                                cdm.id::text ilike '%{}%' or
                                cem.budget_no like '%{}%' or 
                                cem.purpose_code like '%{}%' or 
                                cdm.return_on_investment like '%{}%') order by cdm.created_at desc""".format(
                    department,plant_name,
                    search_query,
                    search_query,
                    search_query,
                    search_query,
                    search_query,
                )
            # ADMIN VIEW ALL CAPEX
            case "admin_capex_view":
                woosee = ""
                department = ""
                raw_sql_query = """ select
                            cdm.id capex_no,
                            cem.budget_no ,
                            cdm.nature_of_requirement ,
                            cdm.total_cost,
                            cem.purpose_code ,
                            to_char(cdm.requisition_date::timestamp, 'DD-MM-YYYY') requisition_date,
                            cdm.payback_period ,
                            cdm.return_on_investment ,
                            um1.department,
                            cdm.budget_type,
                            cdm.budget_id ,
                            cdm.id capex_id,
                            to_char(cdm.created_at::timestamp, 'DD-MM-YYYY') created_at,
                            concat(um.first_name,' ',um.last_name) capex_current_at,
                            concat(um1.first_name,' ',um1.last_name) capex_raised_by,
                            cdm.capex_status
                            from
                                capex_data_master cdm
                            left join user_management um on
                                cdm.capex_current_at = um.emp_no
                            left join capex_excel_master cem on
                            cem.id = cdm.budget_id 
                            left join user_management um1 on
                            cdm.capex_raised_by =um1.emp_no 
                            where 
                            cdm.delete_flag=false and ((cdm.capex_raised_by like '%{}%' or cdm.capex_current_at like '%{}%' and um1.department like '%{}%') and 
                            (
                                cdm.id::text ilike '%{}%' 
                                or cem.budget_no like '%{}%' 
                                or cem.purpose_code like '%{}%' 
                                or cdm.return_on_investment like '%{}%')) order by cdm.created_at desc ;""".format(
                    woosee,
                    woosee,
                    department,
                    search_query,
                    search_query,
                    search_query,
                    search_query,
                    search_query,
                )
            case _:
                print("nope....")

        with connection.cursor() as cursor:
            cursor.execute(raw_sql_query)
            results = cursor.fetchall()
            rows = [
                dict(zip([col[0] for col in cursor.description], row))
                for row in results
            ]
        paginator = PageNumberPagination()
        paginator.page_size = 10
        result_page = paginator.paginate_queryset(rows, request)
        return paginator.get_paginated_response(result_page)
    except Exception as e:
        print("error in get_all_capex_data", e)
        return Response({"status": status.HTTP_400_BAD_REQUEST})


# GET BY BUDGET ID
@api_view(["GET", "DELETE", "PUT"])
def get_by_budget_id(request, id):
    match request.method:
        case "GET":
            obj = Capex.objects.get(pk=id)
            serializers = CapexSerializer(obj)
            return Response(
                {"data": serializers.data, "status_code": status.HTTP_200_OK}
            )
        case "PUT":
            try:
                obj = Capex.objects.get(id=id)
                serializers = CapexSerializer(obj, request.data)
                if serializers.is_valid():
                    serializers.save()
                return Response({"status_code": status.HTTP_200_OK})
            except Exception as e:
                return Response({"status_code": status.HTTP_400_BAD_REQUEST})

        case "DELETE":
            try:
                Capex.objects.filter(id=id).update(delete_flag=True)
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


# UPDATE CAPEX
@api_view(["PUT"])
def update_capex(request):
    try:
        obj = Capex1.objects.get(id=request.data["id"])
        serializers = Capex1Serializer(obj, request.data)
        if serializers.is_valid():
            serializers.save()
        print(serializers.errors)
        return Response({"status": status.HTTP_200_OK})
    except Exception as e:
        return Response({"status": status.HTTP_400_BAD_REQUEST})


# GET BY CAPEX ID, PUT BY ID
@api_view(["GET", "PUT", "DELETE"])
def get_by_capex_id(request, id):
    match request.method:
        case "GET":
            obj = Capex1.objects.get(pk=id)
            serializers = Capex1Serializer(obj)
            woosee = request.GET["woosee"]
            view_access = capex_components_view_access(woosee, serializers.data)
            return Response(
                {
                    "data": serializers.data,
                    "status_code": status.HTTP_200_OK,
                    "view_access": view_access,
                }
            )
        case "DELETE":
            try:
                Capex1.objects.filter(id=id).update(delete_flag=True)
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
            req = Capex1.objects.get(pk=id)
            serializers = Capex1Serializer(req)
            user_info = user_details_from_emp_id(request.data["user_no"])

            obj_data = {
                "index": len(serializers.data["approval_flow"]),
                "status": request.data["approver_status"],
                "comments": request.data["approver_comment"],
                "department": user_info["department"],
                "emp_id": (request.data["user_no"]),
                "user_name": "{} {}".format(
                    user_info["first_name"], user_info["last_name"]
                ),
                "time": datetime.now().strftime("%A, %d %b %Y %H:%M"),
                "next_approver": "",
            }

            sql = """ UPDATE capex_data_master SET  approval_flow = approval_flow || %s::jsonb, capex_current_at = %s, capex_status = %s WHERE id = %s;"""

            def check_condition_for_corporate(approver_status):
                row = []
                # approved
                if approver_status == "0":
                    if serializers.data["capex_current_at"] == "15604":
                        return [None, capex_wf_status[3]]
                    else:
                        raised_by = serializers.data["capex_raised_by"]
                        approved_by = request.data["user_no"]

                        data = capex_wf_approvers(serializers.data["capex_wf_id"])
                        for value in data:
                            row.append(value.split("#")[1])
                        row.insert(0, raised_by)
                        capex_current_at = row[row.index(str(approved_by)) + 1]
                        return [capex_current_at, capex_wf_status[0]]

                # rejected
                if approver_status == "1":
                    return [None, capex_wf_status[2]]

                # ask for justification
                if approver_status == "3":
                    justification_by = request.data["user_no"]
                    raised_by = serializers.data["capex_raised_by"]

                    data = capex_wf_approvers(serializers.data["capex_wf_id"])
                    for value in data:
                        row.append(value.split("#")[1])
                    row.insert(0, raised_by)
                    capex_current_at = row[row.index(str(justification_by)) - 1]
                    return [capex_current_at, capex_wf_status[4]]

                # closed
                if approver_status == "2":
                    return [None, capex_wf_status[3]]

            def check_condition_for_plant(approver_status):
                # approved
                if approver_status == "0":
                    if serializers.data["capex_current_at"] == "15604":
                        return [None, capex_wf_status[3]]
                    else:
                        raised_by = serializers.data["capex_raised_by"]
                        approved_by = request.data["user_no"]
                        row = []
                        data = capex_wf_approvers(serializers.data["capex_wf_id"])
                        row = []
                        for value in data:
                            row.append(value.split("#")[1])
                        row.insert(0, raised_by)
                        capex_current_at = row[row.index(str(approved_by)) + 1]
                        return [capex_current_at, capex_wf_status[0]]

                # rejected
                if approver_status == "1":
                    return [None, capex_wf_status[2]]

                # ask for justification
                if approver_status == "3":
                    justification_by = request.data["user_no"]
                    raised_by = serializers.data["capex_raised_by"]
                    row = []
                    data = capex_wf_approvers(serializers.data["capex_wf_id"])
                    for value in data:
                        row.append(value.split("#")[1])
                    row.insert(0, raised_by)
                    capex_current_at = row[row.index(str(justification_by)) - 1]
                    return [capex_current_at, capex_wf_status[4]]

                # closed
                if approver_status == "2":
                    return [None, capex_wf_status[3]]

            match serializers.data["flow_type"]:
                #### FOR PLANT
                case "for_plant":
                    value = check_condition_for_plant(obj_data["status"])
                    next_approver = value[0]
                    obj_data["next_approver"] = value[0]
                    put_execute_sql(
                        sql,
                        obj_data,
                        next_approver,
                        value[1],
                        request.data["capex_id"],
                    )
                    approve_mail_ready_data(serializers, value, obj_data)

                #### FOR CORPORATE
                case "for_corporate":
                    value = check_condition_for_corporate(obj_data["status"])
                    next_approver = value[0]
                    obj_data["next_approver"] = value[0]
                    put_execute_sql(
                        sql,
                        obj_data,
                        next_approver,
                        value[1],
                        request.data["capex_id"],
                    )
                    approve_mail_ready_data(serializers, value, obj_data)

            return Response(
                {"data": serializers.data, "status_code": status.HTTP_200_OK}
            )


def create_mail_ready_data(serializers, capex_current_at):
    try:
        user_info = user_details_from_emp_id(serializers.data["capex_raised_by"])
        user_name = "{} {}".format(
            user_info["first_name"].capitalize(), user_info["last_name"].capitalize()
        )
        user_department = user_info["department"]
        user_email_id = user_info["email_id"]

        next_approver = user_details_from_emp_id(capex_current_at)
        next_approver_email_id = next_approver["email_id"]
        next_approver_user_name = "{} {}".format(
            next_approver["first_name"].capitalize(),
            next_approver["last_name"].capitalize(),
        )

        data = {
            "capex_status": "Raised",
            "assignees_comment": "Please Take Action",
            "nature_of_requirement": serializers.data["nature_of_requirement"],
            "raised_by": user_name,
            "department": user_department,
            "capex_raised_date": serializers.data["created_at"],
            "total_cost": serializers.data["total_cost"],
            "user_email_id": user_email_id,
            "next_approver_emp_id": capex_current_at,
            "next_approver_email_id": next_approver_email_id,
            "next_approver_user_name": next_approver_user_name,
            "capex_id": "",
            "budget_id": "",
            "assignees_comment": "",
            "approved_by": "",
        }
        mail_confirmation(data)
    except Exception as e:
        print("Error in create_mail_ready_data", e)


def approve_mail_ready_data(serializers, value, obj_data):

    # check if user is md
    user_info = user_details_from_emp_id(serializers.data["capex_raised_by"])
    user_email_id = user_info["email_id"]

    if obj_data["emp_id"] != "15604":
        user_name = "{} {}".format(
            user_info["first_name"].capitalize(), user_info["last_name"].capitalize()
        )
        user_department = user_info["department"]

        next_approver = ""
        next_approver_email_id = ""
        next_approver_user_name = ""

        if value[1] != "REJECTED":
            next_approver = user_details_from_emp_id(value[0])
            next_approver_email_id = next_approver["email_id"]
            next_approver_user_name = "{} {}".format(
                next_approver["first_name"].capitalize(),
                next_approver["last_name"].capitalize(),
            )

        data = {
            "capex_status": value[1],
            "assignees_comment": obj_data["comments"],
            "approved_by": obj_data["user_name"],
            "nature_of_requirement": serializers.data["nature_of_requirement"],
            "raised_by": user_name,
            "department": user_department,
            "capex_raised_date": serializers.data["created_at"],
            "total_cost": serializers.data["total_cost"],
            "user_email_id": user_email_id,
            "next_approver_emp_id": value[0],
            "next_approver_email_id": next_approver_email_id,
            "next_approver_user_name": next_approver_user_name,
            "capex_id": serializers.data["id"],
            "budget_id": serializers.data["budget_id"],
        }
        mail_confirmation(data)
    else:
        capex_approved_mail_notification(serializers, user_email_id)


@api_view(["POST"])
def create_new_capex(request):
    try:
        raised_by_emp = request.data["raised_by"]
        data = execute_sql(
            "select * from user_management um where emp_no='{}';".format(raised_by_emp)
        )[0]

        department = data["department"]
        plant_name = data["plant_name"]

        get_capex_flow_info = execute_sql(
            "select * from capex_workflow cw where department like '%{}%' and plant like '%{}%';".format(
                department, plant_name
            )
        )[0]

        which_flow = (
            "for_plant"
            if str(get_capex_flow_info["which_flow"]) == "0"
            else "for_corporate"
        )

        mutable_data = deepcopy(request.data)
        whose_ur_manager = json.loads(get_capex_flow_info["approver"])[0].split("#")[1]
        mutable_data["capex_current_at"] = whose_ur_manager
        mutable_data["capex_status"] = capex_wf_status[0]
        mutable_data["flow_type"] = which_flow
        mutable_data["capex_raised_by"] = mutable_data["raised_by"]
        mutable_data["capex_wf_id"] = str(get_capex_flow_info["id"])

        serializers = Capex1Serializer(data=mutable_data)

        if serializers.is_valid():
            serializers.save()
            create_mail_ready_data(serializers, capex_current_at=whose_ur_manager)
            return Response({"mess": "created", "status": 200})
        else:
            print(serializers.errors)
            return Response({"error": serializers.errors, "status": 400})
    except Exception as e:
        print("error in creating capex", e)
        return Response({"error": "e", "status": 400})


def execute_sql(sql):
    with connection.cursor() as cursor:
        cursor.execute(sql)
        results = cursor.fetchall()
        rows = [
            dict(zip([col[0] for col in cursor.description], row)) for row in results
        ]
    return rows


def put_execute_sql(sql, obj_data, capex_current_at, capex_status, id_value):
    with connection.cursor() as cursor:
        cursor.execute(sql, [Json(obj_data), capex_current_at, capex_status, id_value])
    return True


def capex_components_view_access(woosee, request):
    components = {
        "approval_status": False,
        "status_close": False,
        "submit_btn": False,
        "comments_box": False,
        "update_btn": False,
        "field_to_form": False,
    }
    components["approval_status"] = (
        True if woosee != request["capex_raised_by"] else False
    )
    components["submit_btn"] = True if woosee == request["capex_current_at"] else False
    components["comments_box"] = (
        True if woosee == request["capex_current_at"] else False
    )
    components["approval_status"] = (
        True if woosee == request["capex_current_at"] else False
    )
    components["update_btn"] = (
        True if request["capex_current_at"] == request["capex_raised_by"] else False
    )
    components["field_to_form"] = True if request["capex_status"] == "CLOSED" else False

    return components


def get_capex_admin():
    key_name = "capex_admin"
    data = r.lrange(key_name, 0, -1)
    return data


def capex_approved_mail_notification(serializers, user_email_id):
    try:
        html = """
                  <!DOCTYPE html>
                <html lang="en">  
                <head>
                    <link href="https://fonts.googleapis.com/css?family=Source+Sans+Pro" rel="stylesheet" type="text/css" />
                    <meta charset="UTF-8" />
                    <meta http-equiv="X-UA-Compatible" content="IE=edge" />
                    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
                </head>
                <body style="padding: 1rem; font-family: 'Source Sans Pro', sans-serif;">
                    <div style="display: flex;">
                    <div style="width: 600px; margin-top: 1rem; display: grid; grid-template-columns: auto; gap: 2rem; width:fit-content;border-radius: 10px;padding:2rem">
                        <br />
                        <img src="https://adorwelding.org/Adorhub_uploads/Capex.png" width="800" alt="Conference Header" style="display: flex;justify-content: center;" />
                        <div style="color: #555259; padding: 0 2rem;">
                        <div style="margin-bottom: 1rem;">
                            <br />
                            <div style='display:flex;justify-content: center;'>
                            <span style="font-size: 2rem; font-weight: 700;">Capex Approved</span>
                            </div>
                            <hr />
                            <div style='display:flex;justify-content: center;gap:.5rem'>
                            <span style="font-size: 1rem; font-weight: 500;">Capex Number : </span>
                            <span style="font-size: 1rem; font-weight: 500;">{}</span>
                            </div>
                        </div>
                        <div style="display: flex; gap: 2px; margin-bottom:.5rem;display:flex;justify-content: center;">
                            <strong>Website Link : </strong>
                            <a href="https://ador.net.in/login">ADORHUB</a>
                        </div>
                        </div>
                        <br />
                        <img src="https://adorwelding.org/Adorhub_uploads/Footer.png" width="700" alt="Conference Footer" style="display: flex;justify-content: center;" />
                    </div>
                    </div>
                    <br />
                </body>
                </html>
        """.format(
            serializers.data["id"]
        )
        common_mail_template(
            html=html,
            subject="Adorhub - Capex Approval Notification",
            to_email=[user_email_id],
        )
    except Exception as e:
        print("error in capex_approved_mail_notification", e)


def mail_confirmation(data):
    try:
        load_dotenv()
        from_email = os.getenv("SENDER_EMAIL")
        to_email = data["next_approver_email_id"]
        smtp_server = os.getenv("SMTP_SERVER")
        smtp_port = os.getenv("SMTP_PORT")
        smtp_username = os.getenv("SMTP_USERNAME")
        smtp_password = os.getenv("SMTP_PASSWORD")

        capex_id = data["capex_id"]
        budget_id = data["budget_id"]

        for_md_only = """
        <div>
        <span>Click on the link below to Approve or Reject</span>
         <div style="display: flex; gap: 2px; margin-top:1rem;">
            <a href="{}/capex/md/approval/mail/?type=0&budget_id={}&capex_id={}">Approve</a>
            <a style="display: flex; gap: 2px; margin-left:1rem;" href="{}/capex/md/approval/mail/?type=1&budget_id={}&capex_id={}">Reject</a>
        </div>
        </div>""".format(
            os.getenv("CAPEX_API"),
            budget_id,
            capex_id,
            os.getenv("CAPEX_API"),
            budget_id,
            capex_id,
        )

        for_others = """<div></div>"""

        approval_btn = (
            for_md_only if data["next_approver_emp_id"] == "15604" else for_others
        )

        approved_by = (
            """<div style="display: flex; gap: 2px; margin-bottom: .5rem;">
                            <span>Approved By : </span>
                            <span>{}</span>
                        </div>""".format(
                data["approved_by"]
            )
            if data["approved_by"]
            else """<div></div>"""
        )

        approved_comment = (
            """<div style="display: flex; gap: 2px; margin-bottom: .5rem;">
                            <span>Approver Comment : </span>
                            <span>{}</span>
                        </div>""".format(
                data["assignees_comment"]
            )
            if data["assignees_comment"]
            else """<div></div>"""
        )

        html = """
            <!DOCTYPE html>
                <html lang="en">  
                <head>
                    <link href="https://fonts.googleapis.com/css?family=Source+Sans+Pro" rel="stylesheet" type="text/css" />
                    <meta charset="UTF-8" />
                    <meta http-equiv="X-UA-Compatible" content="IE=edge" />
                    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
                </head>
                
                <body style="padding: 1rem; font-family: 'Source Sans Pro', sans-serif;">
                <span>Hi {},</span>
                    <div style="display: flex;">
                    <div style="width: 600px; margin-top: 1rem; display: grid; grid-template-columns: auto; gap: 2rem; width:fit-content;border-radius: 10px;padding:2rem">
                        <br />
                        <img src="https://adorwelding.org/Adorhub_uploads/Capex.png" width="800" alt="Conference Header" style="display: flex;justify-content: center;" />
                        <div style="color: #555259; padding: 0 2rem;">
                        <div style="margin-bottom: 1rem;">
                            <br />
                            <span style="font-size: 2rem; font-weight: 700;">Capex Details</span>
                            <hr />
                            <span style="font-size: 1.5rem;  text-align: center;">Status :</span>
                            <span style="font-weight: 700; font-size: 1.5rem;text-align: center;">{}</span>
                            <div>
                            <br>
                            </div>
                            <br />
                        </div>
                        <div style="display: flex; gap: 2px; margin-bottom: .5rem;">
                            <span>Nature of requirement : </span>
                            <span>{}</span>
                        </div>
                        <div style="display: flex; gap: 2px; margin-bottom: .5rem;">
                            <span>Raised By : </span>
                            <span>{}</span>
                        </div>
                
                        <div style="display: flex; gap: 2px; margin-bottom: .5rem;">
                            <span>Department : </span>
                            <span>{}</span>
                        </div>
                
                        <div style="display: flex; gap: 2px; margin-bottom: .5rem;">
                            <span>Capex Raised Date : </span>
                            <span>{}</span>
                        </div>
                
                        <div style="display: flex; gap: 2px; margin-bottom: .5rem;">
                            <span>Total Cost (₹ in Lakhs) : </span>
                            <span>{}</span>
                        </div>
                        {}
                        {}
                        <br>
                       {}
                        <br>
                        <div style="display: flex; gap: 2px; margin-bottom:.5rem;">
                            <strong>Link : </strong>
                            <a href="https://ador.net.in/login">ADORHUB</a>
                        </div>
                        </div>
                        <br />
                        <img src="https://adorwelding.org/Adorhub_uploads/Footer.png" width="700" alt="Conference Footer" style="display: flex;justify-content: center;" />
                    </div>
                    </div>
                    <br />
                </body>
                </html>""".format(
            data["next_approver_user_name"],
            data["capex_status"],
            data["nature_of_requirement"],
            data["raised_by"],
            data["department"],
            datetime.strptime(data["capex_raised_date"][0:10], "%Y-%m-%d").strftime(
                "%d-%m-%Y"
            ),
            data["total_cost"],
            approved_by,
            approved_comment,
            approval_btn,
        )

        # Set up the email addresses and password. Please replace below with your email address and password
        email_from = from_email
        password = smtp_password
        email_to = to_email

        # Create a MIMEMultipart class, and set up the From, To, Subject fields
        email_message = MIMEMultipart()
        email_message["From"] = email_from
        email_message["To"] = email_to

        email_message["Subject"] = "Adorhub - Capex Approval Notification"

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


@api_view(["GET"])
def md_approval_on_mail(request):
    try:
        button_option = request.GET["type"]
        budget_id = request.GET["budget_id"]
        capex_id = request.GET["capex_id"]

        # 0 is APPROVE
        # 1 is REJECT

        api_url = "{}/capex/data-capex/{}/".format(os.getenv("CAPEX_API"), capex_id)

        payload = {
            "budget_id": budget_id,
            "capex_id": capex_id,
            "approver_status": "",
            "approver_comment": "",
            "user_no": "15604",
        }

        match button_option:
            case "0":
                payload["approver_status"] = "0"
                payload["approver_comment"] = "Approved from mail"
                requests.put(api_url, json=payload)
                return HttpResponse(notify_md_return_meassage.format("Approved"))

            case "1":
                payload["approver_status"] = "1"
                payload["approver_comment"] = "Rejected from mail"
                requests.put(api_url, json=payload)
                return HttpResponse(notify_md_return_meassage.format("Rejected"))

            case _:
                return HttpResponse(",Something Went Wrong")
    except Exception as e:
        print(e)


notify_md_return_meassage = """
  <!DOCTYPE html>
                <html lang="en">  
                <head>
                    <link href="https://fonts.googleapis.com/css?family=Source+Sans+Pro" rel="stylesheet" type="text/css" />
                    <meta charset="UTF-8" />
                    <meta http-equiv="X-UA-Compatible" content="IE=edge" />
                    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
                </head>
                
                <body style="padding: 1rem; font-family: 'Source Sans Pro', sans-serif;display:flex;justify-content: center;">
                    <div style="display: flex;">
                    <div style="width: 600px; margin-top: 1rem; display: grid; grid-template-columns: auto; gap: 2rem; width:fit-content;border-radius: 10px;padding:2rem">
                        <br />
                        <img src="https://adorwelding.org/Adorhub_uploads/Capex.png" width="800" alt="Conference Header" style="display: flex;justify-content: center;" />
                        <div style="color: #555259; padding: 0 2rem;">
                        <div style="margin-bottom: 1rem;">
                            <br />
                            <div style='display:flex;justify-content: center;'>
                            <span style="font-size: 2rem; font-weight: 700;">Capex {}</span>
                            </div>
                            <hr />
                        </div>
                        <div style="display: flex; gap: 2px; margin-bottom:.5rem;display:flex;justify-content: center;">
                            <strong>Website Link : </strong>
                            <a href="https://ador.net.in/login">ADORHUB</a>
                        </div>
                        </div>
                        <div style="display:flex;justify-content: center;">
                        <address>Please close this tab. Thank you!</address>
                        </div>
                    </div>
                    </div>
                    <br />
                </body>
                </html>
"""


capex_wf_status = {
    0: "INPROGRESS",
    1: "APPROVED",
    2: "REJECTED",
    3: "CLOSED",
    4: "ASK FOR JUSTIFICATION",
}


def capex_wf_approvers(id):
    return json.loads(
        execute_sql(
            "select approver from capex_workflow cw where id::text like '%{}%';".format(
                id
            )
        )[0]["approver"]
    )


@api_view(["GET"])
def get_list_of_user_for_capex_approver(request):
    query = """SELECT DISTINCT CONCAT(manager, '#', manager_code) AS name FROM user_management WHERE user_status = true AND manager_code NOT LIKE '%F%';"""
    with connection.cursor() as cursor:
        cursor.execute(query)
        results = cursor.fetchall()
        rows = [
            dict(zip([col[0] for col in cursor.description], row)) for row in results
        ]
    return Response(rows)


@api_view(["GET"])
def generate_capex_final_pdf(request):
    try:
        budget_id = request.GET["budget_id"]
        capex_id = request.GET["capex_id"]
        raised_by = request.GET["raised_by"]
        budget_data = execute_sql(
            """SELECT 
                id::text, 
                COALESCE(budget_no,'N/A') as budget_no, 
                COALESCE(purpose_code,'N/A') as purpose_code, 
                COALESCE(purpose_description,'N/A') as purpose_description, 
                COALESCE(line_no::text,'N/A') as line_no, 
                COALESCE(plant,'N/A') as plant, 
                COALESCE(dept,'N/A') as dept, 
                COALESCE(capex_group,'N/A') as capex_group, 
                COALESCE(capex_class,'N/A') as capex_class, 
                COALESCE(category,'N/A') as category, 
                COALESCE(asset_description,'N/A') as asset_description, 
                COALESCE(details,'N/A') as details, 
                COALESCE(rate::text,'N/A') as rate, 
                COALESCE(qty::text,'N/A') as qty, 
                COALESCE(uom::text,'N/A') as uom, 
                COALESCE(final_budget::text,'N/A') as final_budget, 
                COALESCE(remarks,'N/A') as remarks, 
                COALESCE(created_at::text,'N/A') as created_at, 
                COALESCE(updated_at::text,'N/A') as updated_at, 
                COALESCE(delete_flag::text,'N/A') as delete_flag, 
                COALESCE(is_active::text,'N/A') as is_active
                FROM capex_excel_master where id='{}'""".format(
                budget_id
            )
        )

        capex_data = execute_sql(
            """     SELECT 
                    id::text, 
                    COALESCE(budget_id::text,'N/A') as budget_id, 
                    COALESCE(nature_of_requirement::text,'N/A') as nature_of_requirement, 
                    COALESCE(purpose::text,'N/A') as purpose, 
                    COALESCE(payback_period::text,'N/A') as payback_period, 
                    COALESCE(capex_for_which_department::text,'N/A') as capex_for_which_department, 
                    COALESCE(return_on_investment::text,'N/A') as return_on_investment, 
                    COALESCE(budget_type::text,'N/A') as budget_type, 
                    COALESCE(requisition_date::text,'N/A') as requisition_date, 
                    COALESCE(total_cost::text,'N/A') as total_cost, 
                    COALESCE(site_delivery_date::text,'N/A') as site_delivery_date, 
                    COALESCE(capex_status::text,'N/A') as capex_status, 
                    COALESCE(installation_date::text,'N/A') as installation_date, 
                    COALESCE(comment1::text,'N/A') as comment1, 
                    COALESCE(comment2::text,'N/A') as comment2, 
                    COALESCE(comment3::text,'N/A') as comment3, 
                    COALESCE(comment4::text,'N/A') as comment4, 
                    COALESCE(comment5::text,'N/A') as comment5, 
                    COALESCE(comment7::text,'N/A') as comment7, 
                    COALESCE(user_file::text,'N/A') as user_file, 
                    COALESCE(comment6::text,'N/A') as comment6, 
                    COALESCE(created_at::text,'N/A') as created_at, 
                    COALESCE(updated_at::text,'N/A') as updated_at, 
                    COALESCE(asset_listings::text,'N/A') as asset_listings, 
                    COALESCE(flow_type::text,'N/A') as flow_type, 
                    COALESCE(approval_flow::text,'N/A') as approval_flow, 
                    COALESCE(capex_raised_by::text,'N/A') as capex_raised_by, 
                    COALESCE(capex_current_at::text,'N/A') as capex_current_at,
                    COALESCE(delete_flag::text,'N/A')  as delete_flag
                    FROM capex_data_master where id='{}'""".format(
                capex_id
            )
        )
        approval_flow = json.loads(capex_data[0]["approval_flow"])

        replacements = {
            "Capex_Id": str(capex_data[0]["id"]),
            "Date": datetime.now().strftime("%d-%m-%Y"),
            "Key User": raised_by.upper(),
            "Department": budget_data[0]["dept"].upper(),
            "Capex Group": capex_data[0]["flow_type"].upper(),
            "Nature of Requirement": capex_data[0]["nature_of_requirement"].upper(),
            "Purpose": capex_data[0]["purpose"].upper(),
            "Location": budget_data[0]["plant"].upper(),
            "Functional Utility/Performance/Usefulness": capex_data[0][
                "comment1"
            ].upper(),
            "Description Of Asset": budget_data[0]["asset_description"].upper(),
            "Supplier's Name with Address": capex_data[0]["comment3"].upper(),
            "total_cost": capex_data[0]["total_cost"],
            "Expected Date of Delivery at Site": str(
                capex_data[0]["site_delivery_date"]
            )[0:10],
            "Budget Type": (
                capex_data[0]["budget_type"].upper()
                if capex_data[0]["budget_type"]
                else "Non Budgeted"
            ),
            "approval_flow": approval_flow,
        }
        return Response({"replacements":replacements,"mess": "ok"})
    except Exception as e:
        return Response({"mess": e})
