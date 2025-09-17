from django.urls import path
from . import auth_views

app_name = 'auth'

urlpatterns = [
    # Authentication endpoints
    path('register/', auth_views.register, name='register'),
    path('login/', auth_views.login, name='login'),
    path('logout/', auth_views.logout, name='logout'),
    path('profile/', auth_views.profile, name='profile'),
    path('refresh/', auth_views.refresh_token, name='refresh'),
]