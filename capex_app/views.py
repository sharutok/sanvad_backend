from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view
from capex_app.models import Capex, Capex1
from capex_app.serializers import CapexSerializer, Capex1Serializer
from rest_framework import status
import pandas as pd
import requests
import os


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
def get_all_data(request):
    obj = Capex.objects.all()
    serializers = CapexSerializer(obj, many=True)
    return Response(serializers.data)


# GET BY ID
@api_view(["GET"])
def get_by_id(request, id):
    match request.method:
        case "GET":
            obj = Capex.objects.get(pk=id)
            serializers = CapexSerializer(obj)
            return Response(
                {"data": serializers.data, "status_code": status.HTTP_200_OK}
            )


@api_view(["POST"])
def create(request):
    try:
        serializers = Capex1Serializer(data=request.data)
        if serializers.is_valid():
            serializers.save()
            return Response({"mess": "created", status: 200})
        else:
            return Response({"error": serializers.errors, "status_code": 400})
    except e:
        print(e)
        return Response({"error": e, "status_code": 400})
