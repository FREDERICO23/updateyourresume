from django.urls import path
from . import views

urlpatterns = [
    # path('payment/monthly/', views.payment_page, name='monthly_payment_page'),
    path('payment/verify/', views.payment_verify, name='payment_verify'),
    path('payment/monthly/', views.payment_page_monthly, name='payment_page_monthly'),
    path('payment/quarterly/', views.payment_page_quarterly, name='payment_page_quarterly'),
    path('payment/yearly/', views.payment_page_yearly, name='payment_page_yearly'),
    path('payment/success/', views.thank_you_page, name='thank_you_page'),  
    path('payment-page/', views.payment_page, name='payment_page'),
    path('upgrade/', views.upgrade, name='upgrade'),
    path('subscription-details/', views.subscription_details, name='subscription'),



    

]
