from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('predict/<str:company_name>/', views.predict, name='predict'),
    path('history/', views.history, name='history'),
    path('old_predictions/', views.old_predictions, name='old_predictions'),
    path('old_predictions/edit/<int:pk>/', views.edit_prediction, name='edit_prediction'),
    path('old_predictions/delete/<int:pk>/', views.delete_prediction, name='delete_prediction'),
    path('company_history/<str:company_name>/', views.company_history, name='company_history'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),
]
