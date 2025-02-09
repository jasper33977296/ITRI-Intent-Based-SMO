"""
URL configuration for main project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import os
from django.contrib import admin
from django.urls import path, include

CONVERSATION_API_VERSION = os.environ.get('CONVERSATION_MGT_API_VERSION', 'v1.0')
WORKFLOW_API_VERSION = os.environ.get('WORKFLOW_MGT_API_VERSION', 'v1.0')
TOPIC_API_VERSION = os.environ.get('TOPIC_MGT_API_VERSION', 'v1.0')
METADATA_API_VERSION = os.environ.get('METADATA_MGT_API_VERSION', 'v1.0')

urlpatterns = [
    path(f'api/{CONVERSATION_API_VERSION}/', include('main.apps.conversation_mgt.api.urls')),
    path(f'api/{WORKFLOW_API_VERSION}/', include('main.apps.workflow_mgt.api.urls')),
    path(f'api/{TOPIC_API_VERSION}/', include('main.apps.topic_mgt.api.urls')),
    path(f'api/{METADATA_API_VERSION}/', include('main.apps.metadata_mgt.api.urls')),
    path('admin/', admin.site.urls),
]
