from django.urls import path
from main.apps.conversation_mgt.actors.ConversationManager import ConversationManager
from main.apps.conversation_mgt.actors.TextManager import TextManager
urlpatterns = [
    path("conversation_mgt/ConversationManager/create_conversation",ConversationManager.create_conversation,name='create_conversation'),
    path("conversation_mgt/ConversationManager/get_conversation_list",ConversationManager.get_conversation_list,name='get_conversation_list'),
    path("conversation_mgt/ConversationManager/delete_conversation",ConversationManager.delete_conversation,name='delete_conversation'),
    path("conversation_mgt/TextManager/create_text",TextManager.create_text,name='create_text'), #test
    path("conversation_mgt/TextManager/get_text_list",TextManager.get_text_list,name='get_text_list'), #test
]