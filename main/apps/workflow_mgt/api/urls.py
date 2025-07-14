from django.urls import path
from main.apps.workflow_mgt.actors.WorkflowManager import WorkflowManager
from main.apps.workflow_mgt.actors.Consumer import Consumer
from main.apps.workflow_mgt.actors.Producer import Producer
urlpatterns = [
    path("workflow_mgt/WorkflowManager/execute_workflow",WorkflowManager.execute_workflow,name='execute_workflow'),
    path("workflow_mgt/WorkflowManager/logger_human_in_the_loop",WorkflowManager.logger_human_in_the_loop,name='logger_human_in_the_loop'),
    path("workflow_mgt/WorkflowManager/update_workflow_status",WorkflowManager.update_workflow_status,name='update_workflow_status'),
    path("workflow_mgt/Consumer/send_message",Consumer.send_message,name='send_message'),
    path("workflow_mgt/Producer/dispatch_topic",Producer.dispatch_topic,name='dispatch_topic'),
]