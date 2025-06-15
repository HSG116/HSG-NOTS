from django.urls import path
from . import views

app_name = 'ai_assistant'

urlpatterns = [
    path('chat/', views.chat_view, name='chat'),
    path('chat/<int:conversation_id>/', views.chat_view, name='chat_conversation'),
    path('api/send-message/', views.send_message_api, name='send_message'),
    path('api/conversations/', views.conversations_api, name='conversations'),
    path('conversations/', views.conversation_list_view, name='conversation_list'),
    path('conversations/<int:pk>/delete/', views.delete_conversation, name='delete_conversation'),
    path('suggestions/', views.task_suggestions_view, name='task_suggestions'),
    path('suggestions/<int:pk>/accept/', views.accept_suggestion, name='accept_suggestion'),
    path('usage-stats/', views.usage_stats_view, name='usage_stats'),
]
