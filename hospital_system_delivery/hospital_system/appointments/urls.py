from django.urls import path
from . import views

app_name = 'appointments'

urlpatterns = [
    path('', views.appointment_list, name='list'),
    path('add/', views.appointment_create, name='create'),
    path('<int:pk>/status/<str:new_status>/', views.appointment_update_status, name='update_status'),
]
