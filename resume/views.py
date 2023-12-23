import openai
from django.contrib.auth import get_user_model
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.conf import settings

import asyncio
import json
import fitz 
import docx

from azure.storage.blob import BlobServiceClient
import azure.storage.blob as azureblob

from .models import GeneratedResume, GeneratedCoverLetter
from .utils import render_to_pdf, render_to_word, extract_text_from_pdf, extract_text_from_docx

CustomUser = get_user_model()
openai.api_key = ('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')


@require_POST
def save_generated_resume(request):
    if request.method == 'POST':
        updated_content = request.POST.get('updated_content')

        # Get the existing record if it exists, otherwise create a new one
        generated_resume, created = GeneratedResume.objects.get_or_create(
            resume_id=generate_resume.id,  # Replace this with your identifier
            defaults={'content': updated_content}
        )

        # Update the content if the record exists
        if not created:
            generated_resume.content = updated_content
            generated_resume.save()

        return JsonResponse({'success': True})  

    return JsonResponse({'success': False})  

def generate_pdf(request):
   context = {'resume_content': 'resume data'} 
   pdf = render_to_pdf('resume_display.html', context)
   # return HttpReponse for pdf
   if pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="resume.pdf"'
        return response
    
   return HttpResponse("Failed to generate PDF", status=400)
   
def generate_docx(request):
   context = {'resume_content': 'resume data'}  
   docx = render_to_word('resume_display.html', context) 
   # return HttpReponse for docx
   if docx:
        return docx
   return HttpResponse("Failed to generate DOCX", status=400)

@login_required
def generate_resume(request):
    if request.method == "POST":
        # Get user inputs from the form
        job_title = request.POST.get("job_title")
        job_description = request.POST.get("job_description")
        existing_resume = request.POST.get("existing_resume_text")
        existing_resume_file = request.FILES.get("existing_resume_file")       
        
        file_name = existing_resume_file.name

        # If an existing resume file is uploaded, read the content
        if existing_resume_file:

            blob_service = BlobServiceClient.from_connection_string(settings.AZURE_STORAGE_CONNECTION_STRING) 
            blob_client = blob_service.get_blob_client(settings.AZURE_STORAGE_CONTAINER, existing_resume_file.name) 

           # Upload in-memory file to blob    
            data = existing_resume_file.read()
            blob_client.upload_blob(data, length=len(data))

            azure_path = f"https://{settings.AZURE_STORAGE_ACCOUNT}.blob.core.windows.net/{settings.AZURE_STORAGE_CONTAINER}/{existing_resume_file.name}"

            if existing_resume_file.name.endswith('.pdf'):
                try:
                    existing_resume_text = extract_text_from_pdf(azure_path, file_name) 
                except Exception as e:
                    print("PDF text extraction failed", e)

            elif existing_resume_file.name.endswith('.docx'):
                try:
                    existing_resume_text = extract_text_from_docx(azure_path) 
                    print(existing_resume_text)

                except Exception as e:
                    print("PDF text extraction failed", e)
            else:
                existing_resume_text = existing_resume_text
            
            blob_client.delete_blob()

       
        # Create a prompt for expert resume revamp
        prompt = f"""
        
        Task: Generate a professionally styled, ATS-compliant resume tailored to the provided job title, job description, and the existing resume. The aim is to optimize the resume to increase its compatibility with ATS systems, while creatively adjusting certain sections to better align with the job requirements.

        Instructions: Be creative to generate related achievements on the job experiences of the existing resume and skills from the job description.

        Input Data:

        Job Title: {job_title}
        Job Description: {job_description}
        Existing Resume: {existing_resume_text}
        Adjustments:

        From the job description, extract the following in details: name, email, phone, summary, experience, education, skills and interests.
        You will return a jSON response of the details using the keys:  name, contactDetails: "email, phone, linkedin", summary, experience:"title,company,dates,responsibilities(create a list)", education:"level, school, dates", skills(create a list), interests(create a list).

        You will also improve the resume details like; interests, skills, experience title and responsibilities to match the job description to the latter.         
        
        """
        # Call the OpenAI API to generate the resume
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert resume writer.You only return and reply with valid, iterable RFC8259 compliant JSON in your responses"},
                {"role": "user", "content": prompt}

            ]    
        )    
        
        generated_text = response.choices[0].message.content
        user = request.user
        if isinstance(user, CustomUser):
            generated_resume = GeneratedResume(
                user=user,
                job_title=job_title,
                job_description=job_description,
                existing_resume=existing_resume_file,
                generated_text=generated_text
            )
            generated_resume.save()
            
            return redirect('resume_display', resume_id=generated_resume.id)

        else: 
            pass
        
        context = {
            'resume_id': generated_resume.id,
        }
        print(generated_resume.id)
        return redirect("havard_resume", context)  
    
    return render(request, "generate_resume_form.html") 

def resume_display(request, resume_id):
    resume = get_object_or_404(GeneratedResume, id=resume_id)
    
    try:
        generated_text = json.loads(resume.generated_text)
    except json.JSONDecodeError:
        generated_text = {} 

    if request.method == 'POST':
        # Handle download request
        response = HttpResponse(resume.generated_text, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename=generated_resume.pdf'
        return response  
    
    context = {
        'resume': resume,
        'generated_text': generated_text,
        'resume_id' : resume_id,
    }  
    return render(request, 'resume_display.html', context)

def havard_resume(request, resume_id):
    resume = get_object_or_404(GeneratedResume, id=resume_id)
    
    try:
        generated_text = json.loads(resume.generated_text)
    except json.JSONDecodeError:
        generated_text = {} 

    if request.method == 'POST':
        # Handle download request
        response = HttpResponse(resume.generated_text, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename=generated_resume.pdf'
        return response  
    
    context = {
        'resume': resume,
        'generated_text': generated_text,
        'resume_id' : resume_id,
    }  
    return render(request, 'havard_resume.html', context)

def generate_cover_letter(request, resume_id):
    # Retrieve the generated resume
    generated_resume = get_object_or_404(GeneratedResume, id=resume_id)

    cover_letter_prompt = f"""
    Task: Generate a tailored cover letter based on the information extracted from the generated resume and job description.

    Instructions:
    
    Input Data:
    Generated Resume Text: {generated_resume.generated_text}
    Job Description: {generated_resume.job_description}

    Cover Letter Content:

    Introduction: Address the hiring manager or employer with a polite salutation expressing your interest in the position and briefly mention where you learned about the job opening.
    Make sure to highlight a key accomplishment or skill from your resume to capture attention.
    
    Body: Provide a brief overview of your professional background and experiences.
    Emphasize how your skills and experiences align with the requirements of the job.
    Reference specific achievements or projects mentioned in the Generated Resume Text.
    Express enthusiasm for the opportunity and explain why you are a suitable candidate.
    Closing:

    Express appreciation for considering your application. Mention your eagerness to further discuss your qualifications in an interview.
    Include a polite closing statement and express anticipation for a positive response.
    
    Note: Use the generated resume text and job description to tailor the cover letter content, ensuring a cohesive and compelling narrative that aligns with the specific job requirements.


    """

    # if request.method == "POST":
    # Generate cover letter from the resume text
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-1106",
            messages=[
            {"role": "system", "content": "You are an expert cover letter writer.You write cover letters that melt the recruiters to give you the job."},
            {"role": "user", "content": cover_letter_prompt}
        ]
    )
    generated_cover_letter_text = response.choices[0].message.content

    # Store the generated cover letter in the database
    generated_cover_letter = GeneratedCoverLetter(
        user=request.user, 
        generated_resume=generated_resume,
        generated_text=generated_cover_letter_text
    )
    generated_cover_letter.save()

    # Redirect to a page to display or download the generated cover letter
    return redirect('cover_letter_display', cover_letter_id=generated_cover_letter.id)

    
def cover_letter_display(request, cover_letter_id):
    cover_letter = get_object_or_404(GeneratedCoverLetter, id=cover_letter_id)         
    return render(request, 'cover_letter_display.html', {'cover_letter': cover_letter})

def user_resumes(request):
    # Get generated resumes for user 
    resumes = GeneratedResume.objects.filter(user=request.user)
    
    context = {
        'resumes': resumes        
    }
    return render(request, 'user_resumes.html', context)

def display(request):
    return render(request, 'base.html')

def home(request):
    return render(request, 'pages/index.html')

def dashboard(request):
    return render(request, 'dashboard.html')

def genresume(request):
    return render(request, 'generate_resume.html')

def pricing(request):
    return render (request, 'pricing_page.html')