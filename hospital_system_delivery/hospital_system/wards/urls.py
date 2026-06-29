from django.urls import path
from . import views

app_name = 'wards'

urlpatterns = [
    path('admissions/', views.admission_list, name='admission_list'),
    path('admissions/add/', views.admission_create, name='admission_create'),
    path('admissions/<int:pk>/discharge/', views.admission_discharge, name='admission_discharge'),
    path('status/', views.ward_status, name='ward_status'),
]
