from django.urls import path
from main.apps.workflow_mgt.actors.WorkflowManager import WorkflowManager
urlpatterns = [
    path("workflow_mgt/WorkflowManager/execute_workflow",WorkflowManager.execute_workflow,name='execute_workflow'),
]