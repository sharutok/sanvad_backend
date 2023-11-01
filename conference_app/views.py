from django.db import connection
from django.db.models import Q
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.shortcuts import render
from conference_app.models import ConferenceBooking
from conference_app.serializers import ConferenceBookingSerializer
from rest_framework import status
import requests
from datetime import datetime, timedelta
import redis
from rest_framework.pagination import PageNumberPagination


# GET ALL DATA.
@api_view(["GET"])
def all_data(request):
    paginator = PageNumberPagination()
    search_query = request.GET["search"]
    todays_date = request.GET["date"]
    todays_date = (
        ""
        if request.GET["date"] == "false"
        else datetime.now().date().strftime("%Y-%m-%d")
    )
    raw_sql_query = """
                    select
                    	cb.*,
	                    um.first_name ,
	                    um.last_name ,
	                    um.department
                    from
                    	conference_booking cb,user_management um
                    where
                    1=1 and
                    	cb.conf_by = um.emp_no and
                    	 (conf_room LIKE '%{}%'
                        OR conf_by LIKE '%{}%'
                        OR meeting_about LIKE '%{}%') AND conf_end_date::text LIKE '%{}%';""".format(
        search_query, search_query, search_query, todays_date
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
            obj = ConferenceBooking.objects.get(pk=id)
            request.data["delete_flag"] = "Y"
            serializers = ConferenceBookingSerializer(obj, data=request.data)
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
        }

        date1 = datetime.strptime(str(data["conf_end_date"]), "%Y-%m-%d")
        date2 = datetime.strptime(str(data["conf_start_date"]), "%Y-%m-%d")

        # Calculate the difference between the two dates
        delta = date1 - date2

        # Get the number of days as an integer
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

        return Response({"mess": "Created", "status": 200})
    except e as Exception:
        return Response({"mess": "Not", "status": 400, "err": serializers.errors})


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
    r = redis.Redis(host="localhost", port=6379, decode_responses=True)
    key_name = "conference_rooms"
    match request.method:
        # GET ALL DATA
        case "GET":
            data = r.lrange(key_name, 0, -1)
            return Response(data)
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
