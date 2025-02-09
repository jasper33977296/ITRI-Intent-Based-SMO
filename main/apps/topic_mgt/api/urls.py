from django.urls import path
from main.apps.topic_mgt.actors.TopicManager import TopicManager

urlpatterns = [
    path("topic_mgt/TopicManager/init_topic",TopicManager.init_topic,name="init_topic"),
    path("topic_mgt/TopicManager/subscribe_topic",TopicManager.subscribe_topic,name="subscribe_topic"),
    path("topic_mgt/TopicManager/unsubscribe_topic",TopicManager.unsubscribe_topic,name="unsubscribe_topic"),
    path("topic_mgt/TopicManager/get_subscribers",TopicManager.get_subscribers,name="get_subscribers"),
    path("topic_mgt/TopicManager/topic_exists",TopicManager.topic_exists,name="topic_exists"),
    path("topic_mgt/TopicManager/broker_publish",TopicManager.broker_publish,name="broker_publish"),
]