from django.shortcuts import render
import os
import pandas
import json
from rest_framework.response import Response
from rest_framework.decorators import api_view
import mimetypes
from django.http import HttpResponse
from wsgiref.util import FileWrapper
import redis

# Create your views here.


@api_view(["POST"])
def download_excel(request):
    try:
        data = request.data
        out_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "../media/export/"
        )
        pandas.read_json(json.dumps(request.data)).head(100).to_excel(
            out_path + "output.xlsx"
        )

        try:
            # Open the file for reading as binary data
            with open(os.path.join(out_path, "output.xlsx"), "rb") as file:
                # Determine the file's MIME type based on the file extension
                content_type, encoding = mimetypes.guess_type("output.xlsx")
                if content_type is None:
                    content_type = "application/octet-stream"

                # Create an HttpResponse with the file as its content
                response = HttpResponse(FileWrapper(file), content_type=content_type)

                # Set the Content-Disposition header to trigger the download
                response["Content-Disposition"] = 'attachment; filename="output.xlsx"'

                return response
        except FileNotFoundError:
            return HttpResponse("File not found", status=404)
    except Exception as e:
        return Response({"mess": "ok", "error": e})
        print(e)


@api_view(["GET"])
def wether_temp(request):
    r = redis.Redis(host="localhost", port=6379, decode_responses=True)
    return Response({"data": json.loads(r.get("weather_temp"))})
