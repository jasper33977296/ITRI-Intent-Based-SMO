from django.urls import path
from main.apps.conversation_mgt.actors.ConversationManager import ConversationManager
from main.apps.conversation_mgt.actors.TextManager import TextManager
from main.apps.conversation_mgt.actors.ImageManager import ImageManager

urlpatterns = [
    path("conversation_mgt/ConversationManager/create_conversation",ConversationManager.create_conversation,name='create_conversation'),
    path("conversation_mgt/ConversationManager/get_conversation_list",ConversationManager.get_conversation_list,name='get_conversation_list'),
    path("conversation_mgt/ConversationManager/get_agent_conversation_list",ConversationManager.get_agent_conversation_list,name='get_agent_conversation_list'),
    path("conversation_mgt/ConversationManager/delete_conversation",ConversationManager.delete_conversation,name='delete_conversation'),
    path("conversation_mgt/TextManager/create_text",TextManager.create_text,name='create_text'),
    path("conversation_mgt/TextManager/get_text_list",TextManager.get_text_list,name='get_text_list'),
    path("conversation_mgt/TextManager/delete_text",TextManager.delete_text,name='delete_text'),
    path("conversation_mgt/ImageManager/create_image",ImageManager.create_image,name='create_image'),
    path("conversation_mgt/ImageManager/get_image_list",ImageManager.get_image_list,name='get_image_list'),
    path("conversation_mgt/ImageManager/delete_image",ImageManager.delete_image,name='delete_image'),
    path("conversation_mgt/ImageManager/get_image",ImageManager.get_image,name='get_image'),
]