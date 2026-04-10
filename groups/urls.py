from django.urls import path
from . import views

urlpatterns = [
    path('', views.group_list, name='group_list'),
    path('create/', views.create_group, name='create_group'),
    path('join/', views.join_private_group, name='join_private_group'),
    path('<int:group_id>/', views.group_chat, name='group_chat'),
    path('<int:group_id>/leave/', views.leave_group, name='leave_group'),
]
