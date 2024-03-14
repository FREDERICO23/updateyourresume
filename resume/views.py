import openai
import os
from django.contrib.auth import get_user_model
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.conf import settings

import asyncio
import json
import docx

from azure.storage.blob import BlobServiceClient
import azure.storage.blob as azureblob
# import google.generativeai as genai


from .models import GeneratedResume, GeneratedCoverLetter
from .utils import render_to_word, extract_text_from_pdf, extract_text_from_docx

CustomUser = get_user_model()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
openai.api_key = OPENAI_API_KEY

# GOOGLE_API_KEY = os.getenv('GEMINI_API_KEY')
# genai.configure(api_key=GOOGLE_API_KEY)

# Set up the model
# generation_config = {
#   "temperature": 0.92,
#   "top_p": 0.85,
#   "top_k": 1,
#   "max_output_tokens": 1500,
# }

# safety_settings = [
#   {
#     "category": "HARM_CATEGORY_HARASSMENT",
#     "threshold": "BLOCK_MEDIUM_AND_ABOVE"
#   },
#   {
#     "category": "HARM_CATEGORY_HATE_SPEECH",
#     "threshold": "BLOCK_MEDIUM_AND_ABOVE"
#   },
#   {
#     "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
#     "threshold": "BLOCK_MEDIUM_AND_ABOVE"
#   },
#   {
#     "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
#     "threshold": "BLOCK_MEDIUM_AND_ABOVE"
#   },
# ]

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

        print(existing_resume_text)

        # Create a prompt for expert resume revamp
        prompt = f"""        
            Rewrite this resume: ({existing_resume_text}) to fit a {job_title} role based on the provided information (update the responsibilities and skills in every experience to match the role)

            Job Description: ({job_description})
            Desired Keys: name, contactDetails (email, phone, linkedin), summary, experience (title, company, dates, responsibilities), education (level, school, dates), skills (list), interests (list), achievements (list)

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
        # Create a generative model using gemini-pro
        # model = genai.GenerativeModel(
        #     model_name="gemini-pro",
        #     generation_config=generation_config, 
        #     safety_settings=safety_settings
        # )

        # # Generate content using the model
        # response = model.generate_content(prompt)
        # generated_text = response.text
        # user = request.user

        if isinstance(user, CustomUser):
            generated_resume = GeneratedResume(
                user=user,
                job_title=job_title,
                job_description=job_description,
                existing_resume=existing_resume_file,
                generated_text=generated_text
            )
            generated_resume.save()
            print(generated_resume)
            print(generated_text)

            return redirect('havard_resume', resume_id=generated_resume.id)

        else: 
            pass
        
        context = {
            'resume_id': generated_resume.id,
        }
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
    print(context)
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
    Adjustments: return the data in paragraphs.
    """
    # Generate cover letter from the resume text
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-1106",
            messages=[
            {"role": "system", "content": "You are an expert cover letter writer.You write cover letters that melt the recruiters to give you the job."},
            {"role": "user", "content": cover_letter_prompt}
        ]
    )
    generated_cover_letter_text = response.choices[0].message.content

    # Generate cover letter from the resume text
    # model = genai.GenerativeModel(
    #     model_name="gemini-pro",
    #     generation_config=generation_config, 
    #     safety_settings=safety_settings
    # )

    # # Generate content using the model
    # response = model.generate_content(cover_letter_prompt)
    # generated_cover_letter_text = response.text
    
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

def select_resumes(request):
    return render(request, 'resumes.html')

def display(request):
    return render(request, 'base.html')

def index(request):
    return render(request, 'pages/index.html')

def home(request):
    return render(request, 'home.html')

def dashboard(request):
    return render(request, 'dashboard.html')

def genresume(request):
    return render(request, 'generate_resume.html')

def pricing(request):
    return render (request, 'pricing_page.html')