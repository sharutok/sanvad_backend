from rest_framework import pagination


class UserManagementPagination(pagination.PageNumberPagination):
    page_size = 10
