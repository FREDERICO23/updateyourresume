from django.urls import path
from . import views

urlpatterns = [
    path('payment/monthly/', views.payment_page, name='monthly_payment_page'),
    path('payment/verify/', views.payment_verify, name='payment_verify'),
    path('thank-you/', views.thank_you_page, name='thank_you_page'),  
    

]
