from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

import requests
from .models import Profile

CustomUser = get_user_model()

def initialize_payment(request, amount, plan_code, callback_url):
    email = request.user.email  # Get the user's email

    headers = {
        'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
    }
    data = {
        'email': email,
        'amount': amount,  # Amount in cents
        'plan': plan_code,
        'callback_url': callback_url,
    }

    response = requests.post('https://api.paystack.co/transaction/initialize', headers=headers, data=data)
    res_json = response.json()

    if res_json.get('status'):
        authorization_url = res_json['data']['authorization_url']
        return redirect(authorization_url)
    else:
        return render(request, 'payment.html', {'error': res_json.get('message')})


@login_required
def payment_page_monthly(request):
    if request.method == 'POST':
        amount = 1000  # $10 in cents (for USD)
        plan_code = settings.PLN_MONTHLY_CODE
        callback_url = request.build_absolute_uri(reverse('payment_verify')) + '?plan=monthly'
        return initialize_payment(request, amount, plan_code, callback_url)

    return render(request, 'payment_page_monthly.html')

@login_required
def payment_page_quarterly(request):
    if request.method == 'POST':
        amount = 2400  # $24 in cents (for USD)
        plan_code = settings.PLN_QUARTERLY_CODE
        callback_url = request.build_absolute_uri(reverse('payment_verify')) + '?plan=quarterly'
        return initialize_payment(request, amount, plan_code, callback_url)

    return render(request, 'payment_page_quarterly.html')

@login_required
def payment_page_yearly(request):
    if request.method == 'POST':
        amount = 4800  # $48 in cents (for USD)
        plan_code = settings.PLN_YEARLY_CODE
        callback_url = request.build_absolute_uri(reverse('payment_verify')) + '?plan=yearly'
        print(amount, plan_code, callback_url)

        return initialize_payment(request, amount, plan_code, callback_url)
    

    return render(request, 'payment_page_yearly.html')


@login_required
def payment_page(request):
    if request.method == 'POST':
        email = request.user.email  # Get the user's email
        plan = settings.PLN_MONTHLY_CODE    # The plan code for the monthly subscription in USD

        headers = {
            'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
        }
        data = {
            'email': email,
            'amount': 1000,  # $8 in cents (for USD)
            'plan': plan,
            'callback_url': request.build_absolute_uri('/payments/payment/verify/'),
        }

        response = requests.post('https://api.paystack.co/transaction/initialize', headers=headers, data=data)
        res_json = response.json()

        if res_json.get('status'):
            authorization_url = res_json['data']['authorization_url']
            return redirect(authorization_url)
        else:
            return render(request, 'payment_page.html', {'error': res_json.get('message')})

    return render(request, 'payment_page.html')


@login_required
def payment_verify(request):
    print("Payment verify")
    reference = request.GET.get('reference')
    plan = request.GET.get('plan')
    amount = request.GET.get('amount')

    print(reference, plan, amount)
    
    if not reference or not plan:
        return redirect('payment_page')  # Redirect to a general payment page if reference or plan is missing

    headers = {
        'Authorization': f'Bearer {settings.PAYSTACK_TEST_SECRET_KEY}',
    }

    response = requests.get(f'https://api.paystack.co/transaction/verify/{reference}', headers=headers)
    res_json = response.json()

    if res_json.get('status') and res_json['data']['status'] == 'success':
        # Payment was successful, update the user's subscription status
        profile, created = Profile.objects.get_or_create(user=request.user)
        profile.subscription_active = True
        profile.subscribed_plan = plan
        profile.subscription_start_date = timezone.now()
        profile.subscription_price = amount
        
        # # Assuming a monthly plan for simplicity, adjust based on the actual plan
        if plan == 'monthly':
            profile.subscription_expiry_date = timezone.now() + timedelta(days=30)
        elif plan == 'quarterly':
            profile.subscription_expiry_date = timezone.now() + timedelta(days=90)
        elif plan == 'yearly':
            profile.subscription_expiry_date = timezone.now() + timedelta(days=365)
        
        profile.save()

        return redirect('thank_you_page')  # Redirect to the single thank you page after success
    else:
        # Redirect back to the respective payment page based on the plan
        if plan == settings.PLN_MONTHLY_CODE:
            return redirect(reverse('payment_page_monthly'))
        elif plan == settings.PLN_QUARTERLY_CODE:
            return redirect(reverse('payment_page_quarterly'))
        elif plan == settings.PLN_YEARLY_CODE:
            return redirect(reverse('payment_page_yearly'))
        else:
            return redirect('payment_page')  # Fallback to a general payment page if the plan is not recognized


# def payment_verify(request):
#     reference = request.GET.get('reference')
#     if not reference:
#         return redirect('monthly_payment_page')  # Redirect if reference is missing

#     headers = {
#         'Authorization': f'Bearer {settings.PAYSTACK_TEST_SECRET_KEY}',
#     }

#     response = requests.get(f'https://api.paystack.co/transaction/verify/{reference}', headers=headers)
#     res_json = response.json()

#     if res_json.get('status') and res_json['data']['status'] == 'success':
#         # Payment was successful, update the user's subscription status
#         profile, created = Profile.objects.get_or_create(user=request.user)
#         profile.subscription_active = True
#         profile.save()

#         return redirect('thank_you_page')  # Redirect to thank you page after success
#     else:
#         return redirect('monthly_payment_page')  # Redirect to payment page on failure

@login_required
def subscription_details(request):
    try:
        profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        profile = None

    context = {
        'profile': profile,
        'is_subscribed': profile.subscription_active if profile else False,
        'subscribed_plan': profile.subscribed_plan,
        'subscription_start_date': profile.subscription_start_date,
        'subscription_expiry_date': profile.subscription_expiry_date,
        'subscription_price': profile.subscription_price,
        'resume_count': profile.resume_count if profile else 0,
        'cover_letter_count': profile.cover_letter_count if profile else 0,
        'last_reset_date': profile.last_reset_date if profile else None,
    }

    return render(request, 'subscription_details.html', context)

@login_required
def unsubscribe(request):
    profile = Profile.objects.get(user=request.user)
    if profile.subscription_active:
        profile.subscription_active = False
        profile.subscribed_plan = None
        profile.subscription_start_date = None
        profile.subscription_expiry_date = None
        profile.save()
        # To notify the user via email
       
    return redirect(reverse('home'))

@login_required
def upgrade(request):
    return render(request, 'payment.html')

@login_required
def thank_you_page(request):
    return render(request, 'thank_you.html')
