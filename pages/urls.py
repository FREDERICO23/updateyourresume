from django.urls import path

from .views import HomePageView, AboutPageView, GenerateView

urlpatterns = [
    path("", HomePageView.as_view(), name="home"),
    path("about/", AboutPageView.as_view(), name="about"),
    path('generate_resume', GenerateView.as_view(), name="generate_resume")
]
