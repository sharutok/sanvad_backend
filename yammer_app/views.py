from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.shortcuts import render
from rest_framework import status
import requests
import redis
import json


@api_view(["GET"])
def get_api(request):
    try:
        r = redis.Redis(host="localhost", port=6379, decode_responses=True)
        return Response({"data": json.loads(r.get("yammer_data"))})
    except e:
        print("error", e)
        return Response({"error": e})
