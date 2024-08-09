from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.conf import settings
import requests
from .models import Profile
from django.contrib.auth import get_user_model
CustomUser = get_user_model()


@login_required
def payment_page(request):
    if request.method == 'POST':
        email = request.user.email  # Get the user's email
        plan = settings.PLN_MONTHLY_CODE    # The plan code for the monthly subscription in USD

        headers = {
            'Authorization': f'Bearer {settings.PAYSTACK_TEST_SECRET_KEY}',
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
    reference = request.GET.get('reference')
    if not reference:
        return redirect('monthly_payment_page')  # Redirect if reference is missing

    headers = {
        'Authorization': f'Bearer {settings.PAYSTACK_TEST_SECRET_KEY}',
    }

    response = requests.get(f'https://api.paystack.co/transaction/verify/{reference}', headers=headers)
    res_json = response.json()

    if res_json.get('status') and res_json['data']['status'] == 'success':
        # Payment was successful, update the user's subscription status
        profile, created = Profile.objects.get_or_create(user=request.user)
        profile.subscription_active = True
        profile.save()
        
        return redirect('thank_you_page')  # Redirect to thank you page after success
    else:
        return redirect('monthly_payment_page')  # Redirect to payment page on failure


# @login_required
# def payment_verify(request):
#     reference = request.GET.get('reference')
#     headers = {
#         'Authorization': f'Bearer {settings.PAYSTACK_TEST_SECRET_KEY}',
#     }

#     response = requests.get(f'https://api.paystack.co/transaction/verify/{reference}', headers=headers)
#     res_json = response.json()

#     if res_json.get('status') and res_json['data']['status'] == 'success':
#         # Payment was successful
#         user = request.user
#         user.profile.subscription_active = True  # Assuming you have a profile model with this field
#         user.profile.save()
#         return redirect('thank_you_page')
#     else:
#         # Payment failed or was unsuccessful
#         return redirect('payment_page')

@login_required
def thank_you_page(request):
    return render(request, 'thank_you.html')
