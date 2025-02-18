from django.urls import path
from main.apps.metadata_mgt.actors.UserManager import UserManager
from main.apps.metadata_mgt.actors.ConversationManager import ConversationManager
from main.apps.metadata_mgt.actors.TextManager import TextManager
from main.apps.metadata_mgt.actors.WorkflowManager import WorkflowManager
from main.apps.metadata_mgt.actors.ScenarioManager import ScenarioManager
from main.apps.metadata_mgt.actors.ApiFlowManager import ApiFlowManager
from main.apps.metadata_mgt.actors.ApiFlowStepManager import ApiFlowStepManager
from main.apps.metadata_mgt.actors.FieldManager import FieldManager

urlpatterns = [
    path("metadata_mgt/UserManager/create_user",UserManager.create_user,name='create_user'),
    path("metadata_mgt/UserManager/login_user",UserManager.login_user,name='login_user'),
    path("metadata_mgt/UserManager/delete_user",UserManager.delete_user,name='delete_user'),
    path('metadata_mgt/ConversationManager/create_conversation_metadata', ConversationManager.create_conversation_metadata,name='create_conversation_metadata'),
    path('metadata_mgt/ConversationManager/get_conversation_metadata_list', ConversationManager.get_conversation_metadata_list,name='get_conversation_metadata_list'),
    path('metadata_mgt/ConversationManager/get_conversation_metadata', ConversationManager.get_conversation_metadata,name='get_conversation_metadata'),
    path('metadata_mgt/ConversationManager/update_conversation_name', ConversationManager.update_conversation_name,name='update_conversation_name'),    
    path('metadata_mgt/ConversationManager/delete_conversation_metadata', ConversationManager.delete_conversation_metadata,name='delete_conversation_metadata'),
    path('metadata_mgt/TextManager/create_text_metadata', TextManager.create_text_metadata,name='create_text_metadata'),
    path('metadata_mgt/TextManager/delete_text_metadata', TextManager.delete_text_metadata,name='delete_text_metadata'),
    path('metadata_mgt/WorkflowManager/create_workflow_metadata', WorkflowManager.create_workflow_metadata,name='create_workflow_metadata'),
    path('metadata_mgt/WorkflowManager/get_workflow_metadata', WorkflowManager.get_workflow_metadata,name='get_workflow_metadata'),
    path('metadata_mgt/WorkflowManager/update_workflow_metadata', WorkflowManager.update_workflow_metadata,name='update_workflow_metadata'),
    path('metadata_mgt/WorkflowManager/delete_workflow_metadata', WorkflowManager.delete_workflow_metadata,name='delete_workflow_metadata'),
    # ------------------------------------------------------------------------
    # 新增 - ScenarioManager
    # ------------------------------------------------------------------------
    path('metadata_mgt/ScenarioManager/create_scenario', ScenarioManager.create_scenario, name='create_scenario'),
    path('metadata_mgt/ScenarioManager/get_scenario_list', ScenarioManager.get_scenario_list, name='get_scenario_list'),
    path('metadata_mgt/ScenarioManager/get_scenario', ScenarioManager.get_scenario, name='get_scenario'),
    path('metadata_mgt/ScenarioManager/update_scenario', ScenarioManager.update_scenario, name='update_scenario'),
    path('metadata_mgt/ScenarioManager/delete_scenario', ScenarioManager.delete_scenario, name='delete_scenario'),
    path('metadata_mgt/ScenarioManager/get_scenario_details', ScenarioManager.get_scenario_details, name='get_scenario_details'),
    
    # ------------------------------------------------------------------------
    # 新增 - ApiFlowManager
    # ------------------------------------------------------------------------
    path('metadata_mgt/ApiFlowManager/create_api_flow', ApiFlowManager.create_api_flow, name='create_api_flow'),
    path('metadata_mgt/ApiFlowManager/get_api_flow_list', ApiFlowManager.get_api_flow_list, name='get_api_flow_list'),
    path('metadata_mgt/ApiFlowManager/get_api_flow', ApiFlowManager.get_api_flow, name='get_api_flow'),
    path('metadata_mgt/ApiFlowManager/update_api_flow', ApiFlowManager.update_api_flow, name='update_api_flow'),
    path('metadata_mgt/ApiFlowManager/delete_api_flow', ApiFlowManager.delete_api_flow, name='delete_api_flow'),

    # ------------------------------------------------------------------------
    # 新增 - ApiFlowStepManager
    # ------------------------------------------------------------------------
    path('metadata_mgt/ApiFlowStepManager/create_api_flow_step', ApiFlowStepManager.create_api_flow_step, name='create_api_flow_step'),
    path('metadata_mgt/ApiFlowStepManager/get_api_flow_step_list', ApiFlowStepManager.get_api_flow_step_list, name='get_api_flow_step_list'),
    path('metadata_mgt/ApiFlowStepManager/get_api_flow_step', ApiFlowStepManager.get_api_flow_step, name='get_api_flow_step'),
    path('metadata_mgt/ApiFlowStepManager/update_api_flow_step', ApiFlowStepManager.update_api_flow_step, name='update_api_flow_step'),
    path('metadata_mgt/ApiFlowStepManager/delete_api_flow_step', ApiFlowStepManager.delete_api_flow_step, name='delete_api_flow_step'),
    path('metadata_mgt/FieldManager/create_field', FieldManager.create_field, name='create_field'),
]