from rest_framework.response import Response
from rest_framework.decorators import api_view
from ticket_app.models import TicketSystemModel, TicketFileUploadModel
from ticket_app.serializers import (
    TicketSytemSerializer,
    TicketFileUploadSerializer,
)

from sanvad_app.models import UserManagement
from sanvad_app.serializers import userManagementSerializer

from rest_framework import status
import requests
from rest_framework.pagination import PageNumberPagination

from sanvad_project.settings import r
import json
import uuid
from psycopg2.extras import Json

from django.contrib import admin
from datetime import datetime
from django.db import connection


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
