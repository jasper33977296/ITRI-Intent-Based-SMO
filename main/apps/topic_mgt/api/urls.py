from django.urls import path
from main.apps.topic_mgt.actors.TopicManager import TopicManager
from main.apps.topic_mgt.actors.Broker import Broker

urlpatterns = [
    path("topic_mgt/TopicManager/create_topic",TopicManager.create_topic,name="create_topic"),
    path("topic_mgt/TopicManager/delete_topic",TopicManager.delete_topic,name="delete_topic"),
    path("topic_mgt/Broker/create_topic",Broker.create_topic,name="create_topic"),
    path("topic_mgt/Broker/delete_topic",Broker.delete_topic,name="delete_topic"),
]