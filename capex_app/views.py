from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view
from capex_app.models import Capex, Capex1
from rest_framework.pagination import PageNumberPagination
from capex_app.serializers import CapexSerializer, Capex1Serializer
from rest_framework import status
import pandas as pd
import requests
import os
import json
from django.db import connection
from ticket_app.views import user_details_from_emp_id, ticket_wf_status
from datetime import datetime
from psycopg2.extras import Json


# READ EXCEL DATA AND PUSH
@api_view(["GET"])
def read_data_excel(request):
    try:
        current_directory = os.path.dirname(os.path.abspath(__file__))
        excel_file_path = os.path.join(current_directory, "capex-example.xlsx")
        print(excel_file_path)
        df = pd.read_excel(excel_file_path)
        json_data = df.to_dict(orient="records")

        for row in json_data:
            serializers = Capex(
                budget_no=row["BUDGET NO"],
                purpose_code=row["PURPOSE CODE"],
                purpose_description=row["PURPOSE"],
                line_no=row["LINE NO"],
                plant=row["LOCATION"],
                dept=row["DEPARTMENT"],
                capex_group=row["CAPEX GROUP"],
                capex_class=row["CLASS"],
                category=row["CATEGORY"],
                asset_description=row["ASSET DESCRIPTION"],
                details=row["DETAILS"],
                rate=row["RATE"],
                qty=row["QTY"],
                uom=row["UOM"],
                final_budget=row["FINAL BUDGET"],
                remarks=row["REMARKS"],
            )
            serializers.save()
        return Response({"mess": "Created", "status": 200})

    except Exception as e:
        print(e)
        return Response({"errors": e})


# GET ALL DATA
@api_view(["GET"])
def get_all_budget_data(request):
    search_query = request.GET["search"]

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
                                and (cem.budget_no like '%{}%' or cem.purpose_code like '%{}%' or cem.purpose_description like '%{}%' or category like '%{}%');""".format(
        search_query, search_query, search_query, search_query
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
    raw_sql_query = """select
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
                            cdm.capex_status
                        from
                        	capex_data_master cdm,
                        	capex_excel_master cem,
                        	user_management um 
                        where
                            1=1 and
                        	cem.id = cdm.budget_id 
                        	and um.emp_no=cdm.capex_current_at 
                        	and (cem.budget_no like '%{}%' or cem.purpose_code like '%{}%' or cdm.return_on_investment like '%{}%' );
    """.format(
        search_query, search_query, search_query
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
    # return Response(serializers.data)


# GET BY BUDGET ID
@api_view(["GET"])
def get_by_budget_id(request, id):
    match request.method:
        case "GET":
            obj = Capex.objects.get(pk=id)
            serializers = CapexSerializer(obj)
            return Response(
                {"data": serializers.data, "status_code": status.HTTP_200_OK}
            )


# GET BY CAPEX ID, PUT BY ID
@api_view(["GET", "PUT"])
def get_by_capex_id(request, id):
    match request.method:
        case "GET":
            obj = Capex1.objects.get(pk=id)
            serializers = Capex1Serializer(obj)

            return Response(
                {"data": serializers.data, "status_code": status.HTTP_200_OK}
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
            match serializers.data["flow_type"]:
                case "for_plant":
                    match len(serializers.data["approval_flow"]):
                        # ticket is with plant head
                        case 0:
                            print(0)
                            d1 = execute_sql(for_plant)
                            obj_data["next_approver"] = ""

                        # ticket is with manufacuring head
                        case 1:
                            print(1)
                            obj_data["next_approver"] = ""
                        # ticket is with finance manager
                        case 2:
                            print(2)
                            # ticket is with md
                            obj_data["next_approver"] = ""
                case "for_corporate":
                    d1 = execute_sql(
                        for_corporate.format(serializers.data["capex_current_at"])
                    )
                    match len(serializers.data["approval_flow"]):
                        # ticket is with department head
                        case 0:
                            next_approver = d1[0]["index_1"].split("#")[1]
                            obj_data["next_approver"] = next_approver
                            print(
                                sql, obj_data, next_approver, request.data["capex_id"]
                            )
                            put_execute_sql(
                                sql,
                                obj_data,
                                next_approver,
                                ticket_wf_status[0],
                                request.data["capex_id"],
                            )

                        # ticket is with finance manager
                        case 1:
                            next_approver = d1[0]["index_2"].split("#")[1]
                            obj_data["next_approver"] = next_approver
                            print(
                                sql, obj_data, next_approver, request.data["capex_id"]
                            )
                            put_execute_sql(
                                sql,
                                obj_data,
                                next_approver,
                                ticket_wf_status[0],
                                request.data["capex_id"],
                            )
                        # ticket is with md
                        case 2:
                            next_approver = ""
                            obj_data["next_approver"] = next_approver
                            print(
                                sql, obj_data, next_approver, request.data["capex_id"]
                            )
                            put_execute_sql(
                                sql,
                                obj_data,
                                next_approver,
                                ticket_wf_status[3],
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

        d1 = execute_sql(for_corporate)
        d2 = execute_sql(for_plant)
        d = "for_plant" if len(d1) < 0 else "for_corporate"

        request.data["capex_current_at"] = whose_ur_manager
        request.data["capex_status"] = ticket_wf_status[0]
        request.data["flow_type"] = d
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


for_corporate = """
                        select * from (select
                	concat( first_name,' ', last_name,'#',emp_no ) as index_0 ,
                	(select concat( first_name,' ', last_name,'#',emp_no ) from user_management um where emp_no ='00645') index_1,
                	(select concat( first_name,' ', last_name,'#',emp_no ) from user_management um where emp_no ='15604') index_2
                    from
                    user_management um
                    where
                	um.manager_code = '15604') bc where bc.index_0 like '%{}%';"""

for_plant = """
                    select * from 
                    ( select
                    concat( first_name,' ', last_name,'#',emp_no )index_0 ,
                    concat(manager,'#',manager_code)index_1,
                    (select concat( first_name,' ', last_name,'#',emp_no ) from user_management um where emp_no ='00645') index_2,
                    (select concat( first_name,' ', last_name,'#',emp_no ) from user_management um where emp_no ='15604') index_3
                    from user_management um where manager_code ='00280' )bc where bc.index_0 like '%{}%';"""
