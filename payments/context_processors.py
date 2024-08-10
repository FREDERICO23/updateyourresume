from .models import Profile

def subscription_status(request):
    if request.user.is_authenticated:
        profile = Profile.objects.filter(user=request.user).first()
        is_subscribed = profile.subscription_active if profile else False
    else:
        is_subscribed = False

    return {
        'is_subscribed': is_subscribed,
    }
