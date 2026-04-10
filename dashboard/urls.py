from django.urls import path
from . import views

urlpatterns = [
    path('', views.user_dashboard, name='dashboard'),
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
]
