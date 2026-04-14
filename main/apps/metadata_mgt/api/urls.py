from django.urls import path
from main.apps.metadata_mgt.actors.UserManager import UserManager
from main.apps.metadata_mgt.actors.ConversationManager import ConversationManager
from main.apps.metadata_mgt.actors.TextManager import TextManager
from main.apps.metadata_mgt.actors.WorkflowManager import WorkflowManager
from main.apps.metadata_mgt.actors.ImageManager import ImageManager
from main.apps.metadata_mgt.actors.AudioManager import AudioManager
from main.apps.metadata_mgt.actors.AgentManager import AgentManager

urlpatterns = [
    path("metadata_mgt/UserManager/create_user",UserManager.create_user,name='create_user'),
    path("metadata_mgt/UserManager/login_user",UserManager.login_user,name='login_user'),
    path("metadata_mgt/UserManager/delete_user",UserManager.delete_user,name='delete_user'),
    path("metadata_mgt/UserManager/get_user",UserManager.get_user,name='get_user'),
    path("metadata_mgt/UserManager/update_user",UserManager.update_user,name='update_user'),
    path('metadata_mgt/ConversationManager/create_conversation_metadata', ConversationManager.create_conversation_metadata,name='create_conversation_metadata'),
    path('metadata_mgt/ConversationManager/get_conversation_metadata_list', ConversationManager.get_conversation_metadata_list,name='get_conversation_metadata_list'),
    path('metadata_mgt/ConversationManager/get_conversation_metadata', ConversationManager.get_conversation_metadata,name='get_conversation_metadata'),
    path('metadata_mgt/ConversationManager/update_conversation_name', ConversationManager.update_conversation_name,name='update_conversation_name'),    
    path('metadata_mgt/ConversationManager/delete_conversation_metadata', ConversationManager.delete_conversation_metadata,name='delete_conversation_metadata'),
    path('metadata_mgt/ConversationManager/verify_conversation_exist', ConversationManager.verify_conversation_exist,name='verify_conversation_exist'),
    path('metadata_mgt/TextManager/create_text_metadata', TextManager.create_text_metadata,name='create_text_metadata'),
    path('metadata_mgt/TextManager/get_text_metadata', TextManager.get_text_metadata,name='get_text_metadata'),
    path('metadata_mgt/TextManager/delete_text_metadata', TextManager.delete_text_metadata,name='delete_text_metadata'),
    path('metadata_mgt/WorkflowManager/create_workflow_metadata', WorkflowManager.create_workflow_metadata,name='create_workflow_metadata'),
    path('metadata_mgt/WorkflowManager/get_workflow_metadata', WorkflowManager.get_workflow_metadata,name='get_workflow_metadata'),
    path('metadata_mgt/WorkflowManager/update_workflow_metadata', WorkflowManager.update_workflow_metadata,name='update_workflow_metadata'),
    path('metadata_mgt/WorkflowManager/delete_workflow_metadata', WorkflowManager.delete_workflow_metadata,name='delete_workflow_metadata'),
    path('metadata_mgt/ImageManager/create_image_metadata', ImageManager.create_image_metadata,name='create_image_metadata'),
    path('metadata_mgt/ImageManager/get_image_metadata', ImageManager.get_image_metadata,name='get_image_metadata'),
    path('metadata_mgt/ImageManager/get_image_metadata_list', ImageManager.get_image_metadata_list,name='get_image_metadata_list'),
    path('metadata_mgt/ImageManager/delete_image_metadata', ImageManager.delete_image_metadata,name='delete_image_metadata'),
    path('metadata_mgt/AudioManager/create_audio_metadata', AudioManager.create_audio_metadata, name='create_audio_metadata'),
    path('metadata_mgt/AudioManager/get_audio_metadata', AudioManager.get_audio_metadata, name='get_audio_metadata'),
    path('metadata_mgt/AudioManager/get_audio_metadata_list', AudioManager.get_audio_metadata_list, name='get_audio_metadata_list'),
    path('metadata_mgt/AudioManager/delete_audio_metadata', AudioManager.delete_audio_metadata, name='delete_audio_metadata'),
    path('metadata_mgt/AgentManager/create_agent_metadata', AgentManager.create_agent_metadata,name='create_agent_metadata'),
    path('metadata_mgt/AgentManager/get_agent_name', AgentManager.get_agent_name,name='get_agent_name'),
    path('metadata_mgt/AgentManager/get_agent_list_metadata', AgentManager.get_agent_list_metadata,name='get_agent_list_metadata'),
    path('metadata_mgt/AgentManager/update_agent_metadata', AgentManager.update_agent_metadata,name='update_agent_metadata'),
    path('metadata_mgt/AgentManager/delete_agent_metadata', AgentManager.delete_agent_metadata,name='delete_agent_metadata'),
]