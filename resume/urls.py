from django.urls import path
from . import views

urlpatterns = [
    path('generate-resume', views.generate_resume, name='generate_resume'),
    path('display/<int:resume_id>/', views.resume_display, name='resume_display'),
    # path('resume/<int:resume_id>/generate-cover-letter/', views.generate_cover_letter, name='generate_cover_letter'),
    path('generate-cover-letter/', views.generate_cover_letter, name='generate_cover_letter'),

    path('cover-letter/<int:cover_letter_id>/', views.cover_letter_display, name='cover_letter_display'),
    path('test/',views.display, name='display' ),
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),



]