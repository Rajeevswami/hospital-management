from django.urls import path
from . import views

app_name = 'billing'

urlpatterns = [
    path('', views.invoice_list, name='invoice_list'),
    path('create/', views.invoice_create_select_patient, name='invoice_create_select'),
    path('create/<int:patient_id>/', views.invoice_create, name='invoice_create'),
    path('<int:pk>/', views.invoice_detail, name='invoice_detail'),
    path('<int:pk>/pay/', views.record_payment, name='record_payment'),
    path('<int:pk>/pdf/', views.invoice_pdf, name='invoice_pdf'),
]
