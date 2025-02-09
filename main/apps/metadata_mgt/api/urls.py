from django.urls import path
from main.apps.metadata_mgt.actors.UserManager import UserManager
from main.apps.metadata_mgt.actors.ConversationManager import ConversationManager
from main.apps.metadata_mgt.actors.TextManager import TextManager
from main.apps.metadata_mgt.actors.WorkflowManager import WorkflowManager

urlpatterns = [
    path("metadata_mgt/UserManager/create_user",UserManager.create_user,name='create_user'),
    path("metadata_mgt/UserManager/login_user",UserManager.login_user,name='login_user'),
    path("metadata_mgt/UserManager/delete_user",UserManager.delete_user,name='delete_user'),
    path('metadata_mgt/ConversationManager/create_conversation_metadata', ConversationManager.create_conversation_metadata,name='create_conversation_metadata'),
    path('metadata_mgt/ConversationManager/get_conversation_metadata_list', ConversationManager.get_user_conversation_list,name='get_conversation_metadata_list'),
    path('metadata_mgt/ConversationManager/get_conversation_metadata', ConversationManager.get_conversation_metadata,name='get_conversation_metadata'),
    path('metadata_mgt/ConversationManager/update_conversation_name', ConversationManager.update_conversation_name,name='update_conversation_name'),    
    path('metadata_mgt/ConversationManager/delete_conversation_metadata', ConversationManager.delete_conversation,name='delete_conversation_metadata'),
    path('metadata_mgt/TextManager/create_text_metadata', TextManager.create_text_metadata,name='create_text_metadata'),
    path('metadata_mgt/TextManager/delete_text_metadata', TextManager.delete_text_metadata,name='delete_text_metadata'),
    path('metadata_mgt/WorkflowManager/create_workflow_metadata', WorkflowManager.create_workflow_metadata,name='create_workflow_metadata'),
    path('metadata_mgt/WorkflowManager/get_workflow_metadata', WorkflowManager.get_workflow_metadata,name='get_workflow_metadata'),
    path('metadata_mgt/WorkflowManager/update_workflow_metadata', WorkflowManager.update_workflow_metadata,name='update_workflow_metadata'),
    path('metadata_mgt/WorkflowManager/delete_workflow_metadata', WorkflowManager.delete_workflow_metadata,name='delete_workflow_metadata'),
]