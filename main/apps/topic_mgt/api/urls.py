from django.urls import path
from main.apps.topic_mgt.actors.TopicManager import TopicManager
from main.apps.topic_mgt.actors.Broker import Broker

urlpatterns = [
    # path("topic_mgt/TopicManager/init_topic",TopicManager.init_topic,name="init_topic"),
    # path("topic_mgt/TopicManager/subscribe_topic",TopicManager.subscribe_topic,name="subscribe_topic"),
    # path("topic_mgt/TopicManager/unsubscribe_topic",TopicManager.unsubscribe_topic,name="unsubscribe_topic"),
    # path("topic_mgt/TopicManager/get_subscribers",TopicManager.get_subscribers,name="get_subscribers"),
    # path("topic_mgt/TopicManager/topic_exists",TopicManager.topic_exists,name="topic_exists"),
    # path("topic_mgt/TopicManager/broker_publish",TopicManager.broker_publish,name="broker_publish"),
    path("topic_mgt/TopicManager/create_topic",TopicManager.create_topic,name="create_topic"),
    path("topic_mgt/TopicManager/delete_topic",TopicManager.delete_topic,name="delete_topic"),
    path("topic_mgt/Broker/create_topic",Broker.create_topic,name="create_topic"),
    path("topic_mgt/Broker/delete_topic",Broker.delete_topic,name="delete_topic"),
]