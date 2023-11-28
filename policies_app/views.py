from django.db.models import Q
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view
from policies_app.models import UploadPolicy
from policies_app.serializers import UploadPolicySerializer
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from datetime import datetime

# Create your views here.


@api_view(["GET"])
def get_all_data(request):
    search_query = request.GET["search"]
    policy_type = request.GET["type"]
    paginator = PageNumberPagination()
    paginator.page_size = 10
    obj = (
        UploadPolicy.objects.all()
        .filter(
            Q(policy_name__icontains=search_query),
            policy_type=policy_type,
        )
        .order_by("-created_at")
    )

    result_page = paginator.paginate_queryset(obj, request)
    serializers = UploadPolicySerializer(result_page, many=True)
    return paginator.get_paginated_response(serializers.data)


@api_view(["POST"])
def create_policy(request):
    try:
        print(request.data)
        serializers = UploadPolicySerializer(data=request.data)
        if serializers.is_valid():
            serializers.save()
        return Response({"status": status.HTTP_200_OK})
    except Exception as e:
        return Response({"status": status.HTTP_400_BAD_REQUEST})
