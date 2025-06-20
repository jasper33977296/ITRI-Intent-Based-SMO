from django.urls import path
from main.apps.workflow_mgt.actors.WorkflowManager import WorkflowManager
urlpatterns = [
    path("workflow_mgt/WorkflowManager/execute_workflow",WorkflowManager.execute_workflow,name='execute_workflow'),
    path("workflow_mgt/WorkflowManager/human_in_the_loop",WorkflowManager.human_in_the_loop,name='human_in_the_loop'),
    path("workflow_mgt/WorkflowManager/logger_human_in_the_loop",WorkflowManager.logger_human_in_the_loop,name='logger_human_in_the_loop'),
]