from django.contrib import admin
from sanvad_app.models import UserManagement
from ticket_app.models import TicketSystemModel

# Register your models here.

admin.site.register(UserManagement)
admin.site.register(TicketSystemModel)
