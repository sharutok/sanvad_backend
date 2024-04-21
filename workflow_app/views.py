import json
import uuid
from datetime import datetime
import requests
from django.contrib import admin
from django.db import connection
from psycopg2.extras import Json
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from sanvad_app.models import UserManagement
from sanvad_app.serializers import userManagementSerializer
from ticket_app.models import TicketFileUploadModel, TicketSystemModel
from ticket_app.serializers import TicketFileUploadSerializer, TicketSytemSerializer
from utils_app.views import select_sql
from sanvad_project.settings import r
from .models import CapexWorkflow
from .serializers import CapexWorkflowSerializer
from rest_framework.pagination import PageNumberPagination


@api_view(["GET", "PUT", "DELETE"])
def ticket_wf_systems(request):
    ##r = redis.Redis(host="localhost", port=6379, decode_responses=True)
    key_name = "ticket_wf_systems"
    match request.method:
        # GET ALL DATA
        case "GET":
            data = r.get(key_name)
            json_data = json.loads(data)
            return Response(json.loads(data))
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


@api_view(["GET", "PUT", "DELETE"])
def ticket_wf_infra(request):
    ##r = redis.Redis(host="localhost", port=6379, decode_responses=True)
    key_name = "ticket_wf_infra"
    match request.method:
        # GET ALL DATA
        case "GET":
            data = r.get(key_name)
            json_data = json.loads(data)
            return Response(json.loads(data))
        # CREATE
        # case "PUT":
        #     r.lpush(key_name, request.data["value"].upper())
        #     data = r.lrange(key_name, 0, -1)
        #     return Response(data)
        # DELETE
        # case "DELETE":
        #     r.lrem(key_name, 0, request.data["value"])
        #     data = r.lrange(key_name, 0, -1)
        #     return Response(data)


@api_view(["GET", "PUT", "DELETE"])
def capex_wf_plant(request):
    ##r = redis.Redis(host="localhost", port=6379, decode_responses=True)
    key_name = "capex_wf_plant"
    match request.method:
        # GET ALL DATA
        case "GET":
            data = r.get(key_name)
            json_data = json.loads(data)
            return Response(json.loads(data))
        # CREATE
        # case "PUT":
        #     r.lpush(key_name, request.data["value"].upper())
        #     data = r.lrange(key_name, 0, -1)
        #     return Response(data)
        # DELETE
        # case "DELETE":
        #     r.lrem(key_name, 0, request.data["value"])
        #     data = r.lrange(key_name, 0, -1)
        #     return Response(data)


@api_view(["GET", "PUT", "DELETE"])
def capex_wf_corporate(request):
    ##r = redis.Redis(host="localhost", port=6379, decode_responses=True)
    key_name = "capex_wf_corporate"
    match request.method:
        # GET ALL DATA
        case "GET":
            data = r.get(key_name)
            json_data = json.loads(data)
            return Response(json.loads(data))
        # CREATE
        # case "PUT":
        #     r.lpush(key_name, request.data["value"].upper())
        #     data = r.lrange(key_name, 0, -1)
        #     return Response(data)
        # DELETE
        # case "DELETE":
        #     r.lrem(key_name, 0, request.data["value"])
        #     data = r.lrange(key_name, 0, -1)
        #     return Response(data)


@api_view(["POST", "GET", "PUT"])
def capex_workflow_operation(request):
    try:
        match request.method:
            case "POST":
                print(request.data)
                is_dept = select_sql(
                    """select count(*) from capex_workflow where department='{}' and plant='{}' """.format(
                        request.data["department"], request.data["plant"]
                    )
                )[0]["count"]
                if int(is_dept) == 0:
                    approver = [
                        request.data["first_approver"],
                        request.data["second_approver"],
                        request.data["third_approver"],
                        request.data["fourth_approver"],
                    ]
                    approver = [x for x in approver if x != ""]
                    request.data["approver"] = approver
                    serializers = CapexWorkflowSerializer(data=request.data)
                    if serializers.is_valid():
                        serializers.save()
                        return Response({"status": 200, "mess": ""})
                    else:
                        print(serializers.errors)
                        return Response({"status": 400, "mess": ""})
                else:
                    return Response(
                        {
                            "status": 400,
                            "mess": "Capex Workflow already exist for this Department!",
                        }
                    )
            case "GET":
                serializers = CapexWorkflowSerializer(
                    CapexWorkflow.objects.filter(department=request.GET["department"]),
                    many=True,
                )
                return Response({"status": 200, "mess": "", "data": serializers.data})
            case "PUT":
                id = request.data["id"]
                serializers = CapexWorkflow.objects.get(id=id)
                request.data["fourth_approver"] = (
                    ""
                    if int(request.data["which_flow"]) == 1
                    else request.data["fourth_approver"]
                )
                approver = [
                    request.data["first_approver"],
                    request.data["second_approver"],
                    request.data["third_approver"],
                    request.data["fourth_approver"],
                ]
                approver = [x for x in approver if x != ""]
                request.data["approver"] = approver
                serializers = CapexWorkflowSerializer(serializers, data=request.data)
                if serializers.is_valid():
                    serializers.save()
                    return Response({"status": 200, "mess": ""})
                else:
                    print(serializers.errors)
                return Response({"status": 400, "mess": ""})
    except Exception as e:
        print("error", e)
        return Response({"status": 400, "mess": ""})


@api_view(["GET"])
def all_capex_wf(request):
    try:
        paginator = PageNumberPagination()
        paginator.page_size = 10
        raw_sql_query = """select
		case 
        	when which_flow ='0' then 'PLANT' 
        	when which_flow ='1' then 'CORPORATE'  
        	else ''
        end as ROLE,
	split_part(replace (approver[0]::text,'"',''),'#',1) as first,
	split_part(replace (approver[1]::text,'"',''),'#',1) as second ,
	split_part(replace (approver[2]::text,'"',''),'#',1) as third ,
	split_part(replace (approver[3]::text,'"',''),'#',1) as fourth,id,department,to_char(created_at::timestamp AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata', 'DD-MM-YYYY') created_at
,COALESCE(plant,'ALL') as plant,which_flow
from
	capex_workflow cw ;"""
        with connection.cursor() as cursor:
            cursor.execute(raw_sql_query)
            results = cursor.fetchall()
            rows = [
                dict(zip([col[0] for col in cursor.description], row))
                for row in results
            ]
        result_page = paginator.paginate_queryset(rows, request)

        return paginator.get_paginated_response(result_page)
    except Exception as e:
        return Response({"status": 400, "mess": e})
