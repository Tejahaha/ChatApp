from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat_list, name='chat_list'),
    path('<int:user_id>/', views.private_chat, name='private_chat'),
]
