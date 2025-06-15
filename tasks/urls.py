from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('list/', views.task_list_view, name='list'),
    path('create/', views.task_create_view, name='create'),
    path('<int:pk>/', views.task_detail_view, name='detail'),
    path('<int:pk>/edit/', views.task_edit_view, name='edit'),
    path('<int:pk>/delete/', views.task_delete_view, name='delete'),
    path('<int:pk>/toggle/', views.task_toggle_status, name='toggle_status'),
    path('calendar/', views.calendar_view, name='calendar'),
    path('categories/', views.category_list_view, name='categories'),
    path('api/tasks/', views.api_tasks_json, name='api_tasks'),
    path('api/categories/', views.api_categories_json, name='api_categories'),
]
