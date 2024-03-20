from django.urls import path, include

from workflow_app.views import (
    ticket_wf_systems,
    ticket_wf_infra,
    capex_wf_plant,
    capex_wf_corporate,capex_workflow_operation
)

urlpatterns = [
    path("ticket/systems/", ticket_wf_systems, name="ticket-wf-systems"),
    path("ticket/infra/", ticket_wf_infra, name="ticket-wf-infra"),
    path("capex/plant/", capex_wf_plant, name="capex-wf-plant"),
    path("capex/corporate/", capex_wf_corporate, name="capex-wf-corporate"),
    path("capex/op/",capex_workflow_operation,name="capex-workflow-operation")    
]
