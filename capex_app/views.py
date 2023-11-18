from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view
from capex_app.models import Capex, Capex1
from rest_framework.pagination import PageNumberPagination
from capex_app.serializers import (
    CapexSerializer,
    Capex1Serializer,
    UploadBudgetSerializer,
)
from rest_framework import status
import pandas as pd
import requests
import redis
import os
import json
from django.db import connection
from ticket_app.views import user_details_from_emp_id, ticket_wf_status
from datetime import datetime
from psycopg2.extras import Json
from sanvad_app.models import UserManagement
from sanvad_app.serializers import userManagementSerializer


# READ EXCEL DATA AND PUSH
@api_view(["POST"])
def read_data_excel(request):
    try:
        serializers = UploadBudgetSerializer(data=request.data)
        obj = ""
        if serializers.is_valid():
            print("file saved")
            obj = serializers.save()

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
            print("data saved")
            serializers.save()
        return Response({"mess": "Created", "status": 200})

    except Exception as e:
        print(e)
        return Response({"errors": e})


# GET ALL DATA
@api_view(["GET"])
def get_all_budget_data(request):
    search_query = request.GET["search"]
    woosee = request.GET["woosee"]

    user_info = UserManagement.objects.get(emp_no=woosee)
    user_info = userManagementSerializer(user_info)

    print(woosee, get_capex_admin())

    plant_name = "" if woosee in get_capex_admin() else user_info.data["plant_name"]
    department = "" if woosee in get_capex_admin() else user_info.data["department"]

    print(plant_name, department, "ppp")

    raw_sql_query = """
                            select
                            	*
                            from
                            	capex_excel_master cem,
                            	(
                            	SELECT
                                cem.id AS budget_id,
                                COALESCE(COUNT(cdm.budget_id), 0) AS no_of_capex,
                                COALESCE(SUM(cdm.total_cost), 0) AS consumed,
                                COALESCE(cem.final_budget, 0) AS final_budget,
                                COALESCE(COALESCE(cem.final_budget, 0) - COALESCE(SUM(cdm.total_cost), 0), 0) AS budget_remaining
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
                                and cem.plant like '%{}%' and cem.dept like '%{}%'
                                and cem.delete_flag=false
                                and (cem.budget_no like '%{}%' or cem.purpose_code like '%{}%' or cem.purpose_description like '%{}%' or category like '%{}%');""".format(
        plant_name, department, search_query, search_query, search_query, search_query
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


@api_view(["GET"])
def get_all_capex_data(request):
    search_query = request.GET["search"]
    woosee = request.GET["woosee"]
    raw_sql_query = """
                            select
	                        cem.budget_no ,
                        	cem.line_no ,
                        	cem.purpose_code ,
                        	cdm.requisition_date ,
                        	cdm.payback_period ,
                        	cdm.return_on_investment ,
                        	cdm.budget_type,
                        	cdm.budget_id ,
                        	cdm.id capex_id,
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
                             cdm.delete_flag=false and (cdm.capex_raised_by like '%{}%' or cdm.capex_current_at like '%{}%' and 
                            (cem.budget_no like '%{}%' or cem.purpose_code like '%{}%' or cdm.return_on_investment like '%{}%') ) ;
    """.format(
        woosee, woosee, search_query, search_query, search_query
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

            sql = """
                    UPDATE capex_data_master
                    SET 
                    approval_flow = approval_flow || %s::jsonb,
                    capex_current_at = %s,
                    capex_status = %s
                    WHERE id = %s;
                    """

            def check_condition_for_corporate(approver_status):
                # approved
                if approver_status == "0":
                    raised_by = serializers.data["capex_raised_by"]
                    approved_by = request.data["user_no"]
                    get_wf = execute_sql(user_flow_for_corporate.format(raised_by))
                    row = []
                    for data in get_wf:
                        for key, value in data.items():
                            row.append(value.split("#")[1])
                    capex_current_at = row[row.index(str(approved_by)) + 1]
                    return [capex_current_at, capex_wf_status[0]]

                # rejected
                if approver_status == "1":
                    return [None, capex_wf_status[2]]

                # ask for justification
                if approver_status == "3":
                    justification_by = request.data["user_no"]
                    raised_by = serializers.data["capex_raised_by"]
                    get_wf = execute_sql(user_flow_for_corporate.format(raised_by))
                    row = []
                    for data in get_wf:
                        for key, value in data.items():
                            row.append((value.split("#")[1]))
                    capex_current_at = row[row.index(str(justification_by)) - 1]
                    return [capex_current_at, capex_wf_status[4]]

                # closed
                if approver_status == "2":
                    return [None, capex_wf_status[3]]

            def check_condition_for_plant(approver_status):
                # approved
                if approver_status == "0":
                    raised_by = serializers.data["capex_raised_by"]
                    approved_by = request.data["user_no"]
                    get_wf = execute_sql(user_flow_for_plant.format(raised_by))
                    row = []
                    for data in get_wf:
                        for key, value in data.items():
                            row.append(value.split("#")[1])
                    capex_current_at = row[row.index(str(approved_by)) + 1]
                    return [capex_current_at, capex_wf_status[0]]

                # rejected
                if approver_status == "1":
                    return [None, capex_wf_status[2]]

                # ask for justification
                if approver_status == "3":
                    justification_by = request.data["user_no"]
                    raised_by = serializers.data["capex_raised_by"]
                    get_wf = execute_sql(user_flow_for_plant.format(raised_by))
                    row = []
                    for data in get_wf:
                        for key, value in data.items():
                            row.append((value.split("#")[1]))
                    capex_current_at = row[row.index(str(justification_by)) - 1]
                    return [capex_current_at, capex_wf_status[4]]

                # closed
                if approver_status == "2":
                    return [None, capex_wf_status[3]]

            match serializers.data["flow_type"]:
                case "for_plant":
                    if len(serializers.data["approval_flow"]):
                        value = check_condition_for_plant(obj_data["status"])
                        print(value)
                        next_approver = value[0]
                        obj_data["next_approver"] = value[0]
                        put_execute_sql(
                            sql,
                            obj_data,
                            next_approver,
                            value[1],
                            request.data["capex_id"],
                        )

                    # flow has not yet started
                    else:
                        value = check_condition_for_plant(obj_data["status"])
                        print(value)
                        next_approver = value[0]
                        obj_data["next_approver"] = value[0]
                        print(value)
                        put_execute_sql(
                            sql,
                            obj_data,
                            next_approver,
                            value[1],
                            request.data["capex_id"],
                        )

                case "for_corporate":
                    # d1 = execute_sql(
                    #     for_corporate.format(serializers.data["capex_current_at"])
                    # )
                    # flow has started
                    if len(serializers.data["approval_flow"]):
                        value = check_condition_for_corporate(obj_data["status"])
                        next_approver = value[0]
                        obj_data["next_approver"] = value[0]
                        print(value)
                        put_execute_sql(
                            sql,
                            obj_data,
                            next_approver,
                            value[1],
                            request.data["capex_id"],
                        )

                    # flow has not yet started
                    else:
                        value = check_condition_for_corporate(obj_data["status"])
                        next_approver = value[0]
                        obj_data["next_approver"] = value[0]
                        print(value)
                        put_execute_sql(
                            sql,
                            obj_data,
                            next_approver,
                            value[1],
                            request.data["capex_id"],
                        )

            return Response(
                {"data": serializers.data, "status_code": status.HTTP_200_OK}
            )


@api_view(["POST"])
def create_new_capex(request):
    try:
        raised_by_emp = request.data["raised_by"]
        whose_ur_manager = user_details_from_emp_id(raised_by_emp)["manager_code"]

        d1 = execute_sql(user_flow_for_plant.format(raised_by_emp))[0]["index_1"]
        d2 = execute_sql(user_flow_for_corporate.format(raised_by_emp))[0]["index_1"]
        d = "for_plant" if d1 else "for_corporate"
        print(d)

        request.data["capex_current_at"] = whose_ur_manager
        request.data["capex_status"] = capex_wf_status[0]
        request.data["flow_type"] = d
        request.data["capex_raised_by"] = request.data["raised_by"]
        serializers = Capex1Serializer(data=request.data)

        if serializers.is_valid():
            serializers.save()
            return Response({"mess": "created", "status": 200})
        else:
            return Response({"error": serializers.errors, "status_code": 400})
    except Exception as e:
        print(e)
        return Response({"error": "e", "status_code": 400})


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


def capex_components_view_access(woosee, request):
    components = {
        "approval_status": False,
        "status_close": False,
        "submit_btn": False,
        "comments_box": False,
    }
    components["approval_status"] = (
        True if woosee != request["capex_raised_by"] else False
    )
    components["submit_btn"] = True if woosee != request["capex_raised_by"] else False
    components["comments_box"] = True if woosee != request["capex_raised_by"] else False
    components["approval_status"] = (
        True if woosee != request["capex_raised_by"] else False
    )

    return components


for_corporate = """
                        select * from (select
                	concat( first_name,' ', last_name,'#',emp_no ) as index_0 ,
                	(select concat( first_name,' ', last_name,'#',emp_no ) from user_management um where emp_no ='00645') index_1,
                	(select concat( first_name,' ', last_name,'#',emp_no ) from user_management um where emp_no ='15604') index_2
                    from
                    user_management um
                    where
                	um.manager_code = '15604') bc where bc.index_0 like '%{}%';"""

user_flow_for_corporate = """
                   select concat(um1.first_name ,' ',um1.last_name ,'#',um1.emp_no)index_0,bc.index_1,bc.index_2,bc.index_3 from user_management um1 left join 
                    (select 			emp_no,
                	concat( first_name,' ', last_name,'#',emp_no ) as index_1 ,
                	(select concat( first_name,' ', last_name,'#',emp_no ) from user_management um where emp_no ='00645') index_2,
                	(select concat( first_name,' ', last_name,'#',emp_no ) from user_management um where emp_no ='15604') index_3
                    from
                    user_management um
                    where
                	um.manager_code = '15604') bc on um1.manager_code =bc.emp_no where  um1.emp_no ='{}'"""

for_plant = """
                    select * from 
                    ( select
                    concat( first_name,' ', last_name,'#',emp_no )index_0 ,
                    concat(manager,'#',manager_code)index_1,
                    (select concat( first_name,' ', last_name,'#',emp_no ) from user_management um where emp_no ='00645') index_2,
                    (select concat( first_name,' ', last_name,'#',emp_no ) from user_management um where emp_no ='15604') index_3
                    from user_management um where manager_code ='00280' )bc where bc.index_0 like '%{}%';"""

user_flow_for_plant = """
                     select concat(um1.first_name ,' ',um1.last_name ,'#',um1.emp_no) index_0,index_1,index_2,index_3,index_4 from user_management um1 left join 
                  ( select
                    emp_no,
                    concat( first_name,' ', last_name,'#',emp_no )index_1 ,
                    concat(manager,'#',manager_code)index_2,
                    (select concat( first_name,' ', last_name,'#',emp_no ) from user_management um where emp_no ='00645') index_3,
                    (select concat( first_name,' ', last_name,'#',emp_no ) from user_management um where emp_no ='15604') index_4
                    from user_management um where manager_code ='00280' )bc on um1.manager_code =bc.emp_no where um1.emp_no ='{}' ;"""


capex_wf_status = {
    0: "INPROGRESS",
    1: "APPROVED",
    2: "REJECTED",
    3: "CLOSED",
    4: "ASK FOR JUSTIFICATION",
}


def get_capex_admin():
    r = redis.Redis(host="localhost", port=6379, decode_responses=True)
    key_name = "capex_admin"
    data = r.lrange(key_name, 0, -1)
    return data
