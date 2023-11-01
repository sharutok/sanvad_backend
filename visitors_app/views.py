from django.db.models import Q
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.shortcuts import render
from visitors_app.models import VisitorsManagement
from visitors_app.serializers import VisitorsManagementSerializer
from rest_framework import status
import requests
from datetime import datetime
from rest_framework.pagination import PageNumberPagination
from django.db import connection


# GET ALL DATA.
@api_view(["GET"])
def all_data(request):
    paginator = PageNumberPagination()
    search_query = request.GET["search"]
    paginator.page_size = 10
    raw_sql_query = """
                          select
                        vm.*,
                        concat(um.first_name,' ',um.last_name)name,
                        um.department,
                        to_char(vm.start_date_time::timestamp, 'DD-MM-YYYY HH12:MI AM') start_date_time ,
	                    to_char(vm.end_date_time ::timestamp, 'DD-MM-YYYY HH12:MI AM') end_date_time 
                        from
                        	visitors_management vm
                        left join user_management um on
                        	vm.raised_by = um.emp_no
                        where vm.reason_for_visit like '%{}%' or vm.raised_by like '%{}%' order by updated_at desc;	""".format(
        search_query, search_query
    )

    with connection.cursor() as cursor:
        cursor.execute(raw_sql_query)
        results = cursor.fetchall()
        rows = [
            dict(zip([col[0] for col in cursor.description], row)) for row in results
        ]
    result_page = paginator.paginate_queryset(rows, request)
    return paginator.get_paginated_response(result_page)


# GET DATA BY ID
# DELETE DATA BY ID
@api_view(["GET", "DELETE"])
def data_by_id(request, id):
    match request.method:
        case "GET":
            raw_sql_query = """
                            select
                            	vm.*,
                            	concat(um.first_name,' ',um.last_name)name,
                            	um.department 
                            from
                            	visitors_management vm
                            left join user_management um on
                            	vm.raised_by = um.emp_no
                            where vm.id='{}';	
                            ;""".format(
                id
            )

            with connection.cursor() as cursor:
                cursor.execute(raw_sql_query)
                results = cursor.fetchall()
                rows = [
                    dict(zip([col[0] for col in cursor.description], row))
                    for row in results
                ]
            return Response({"data": rows, "status_code": status.HTTP_200_OK})
        case "DELETE":
            obj = VisitorsManagement.objects.get(pk=id)
            request.data["delete_flag"] = "Y"
            serializers = VisitorsManagementSerializer(obj, data=request.data)
            if serializers.is_valid():
                serializers.save()
                return Response(
                    {"data": serializers.data, "status_code": status.HTTP_200_OK}
                )
            return Response(
                {
                    "error": serializers.errors,
                    "status_code": status.HTTP_400_BAD_REQUEST,
                }
            )


# CREATE
@api_view(["POST"])
def create(request):
    serializers = VisitorsManagementSerializer(data=request.data)
    if serializers.is_valid():
        serializers.save()
        return Response({"mess": "Created", "status": status.HTTP_200_OK})
    return Response(
        {
            "mess": "Not",
            "status": status.HTTP_400_BAD_REQUEST,
            "err": serializers.errors,
        }
    )
