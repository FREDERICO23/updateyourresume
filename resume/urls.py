from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('home/', views.home, name='home'),
    path('generate-resume', views.generate_resume, name='generate_resume'),
    path('display/<int:resume_id>/', views.resume_display, name='resume_display'),
    path('havard_display/<int:resume_id>/', views.havard_resume, name='havard_resume'),
    path('select-resumes/', views.select_resumes, name='select_resumes'),

    # path('resume/<int:resume_id>/generate-cover-letter/', views.generate_cover_letter, name='generate_cover_letter'),
    path('generate-cover-letter//<int:resume_id>/', views.generate_cover_letter, name='generate_cover_letter'),

    path('cover-letter/<int:cover_letter_id>/', views.cover_letter_display, name='cover_letter_display'),
    path('test/',views.display, name='display' ),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('list-resumes/', views.user_resumes, name="list_resumes"),

    path('generate_docx/', views.generate_docx, name='generate_docx'),
    path('save-generated-resume/', views.save_generated_resume, name='save_generated_resume'),
    path('pricing/', views.pricing, name='pricing'),




]