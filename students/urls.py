from django.urls import path
from django.shortcuts import redirect
from .views import register, login_view, logout_view, dashboard,chatbot

urlpatterns = [
    path('', lambda request: redirect('login')),  # Redirect root to login page
    path('register/', register, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('dashboard/', dashboard, name='dashboard'),
    path('chat/', chatbot, name='chat'),
]
