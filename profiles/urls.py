from django.urls import path
from . import views

urlpatterns = [
    path('search/', views.search_users, name='search_users'),
    path('edit/', views.edit_profile, name='edit_profile'),
    path('block/<int:user_id>/', views.block_user, name='block_user'),
    path('<str:username>/', views.profile_view, name='profile_view'),
]
