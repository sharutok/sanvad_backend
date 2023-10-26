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
    print(search_query)
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
                        	cdm.id capex_id
                        from
                        	capex_data_master cdm,
                        	capex_excel_master cem
                        where
                        	cem.id = cdm.budget_id 
                        	and (cem.budget_no like '%{}%' or	 cem.purpose_code  like '%{}%' or cdm.return_on_investment  like '%{}%' );
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


# GET BY CAPEX ID
@api_view(["GET"])
def get_by_capex_id(request, id):
    match request.method:
        case "GET":
            obj = Capex1.objects.get(pk=id)
            serializers = Capex1Serializer(obj)
            return Response(
                {"data": serializers.data, "status_code": status.HTTP_200_OK}
            )


@api_view(["POST"])
def create_new_capex(request):
    try:
        serializers = Capex1Serializer(data=request.data)
        if serializers.is_valid():
            serializers.save()
            return Response({"mess": "created", status: 200})
        else:
            return Response({"error": serializers.errors, "status_code": 400})
    except Exception as e:
        print(e)
        return Response({"error": "e", "status_code": 400})
