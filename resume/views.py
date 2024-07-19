import openai
import os
from groq import Groq
from django.contrib.auth import get_user_model
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.conf import settings
from django.template.loader import get_template


import asyncio
import json
import docx

from azure.storage.blob import BlobServiceClient
import azure.storage.blob as azureblob

from .models import GeneratedResume, GeneratedCoverLetter
from .utils import render_to_word, extract_text_from_pdf, extract_text_from_docx, html_to_pdf

CustomUser = get_user_model()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
openai.api_key = OPENAI_API_KEY

client = Groq(
    api_key=os.getenv("GROQ_API_KEY"),
)

@login_required
def generate_pdf(request, resume_id):
    resume = get_object_or_404(GeneratedResume, id=resume_id)
    
    try:
        generated_text = json.loads(resume.generated_text)
    except json.JSONDecodeError:
        generated_text = {} 
    
    context = {
        'resume': resume,
        'generated_text': generated_text,
        'resume_id': resume_id,
    }
    name = generated_text['name']
    template = get_template('havard.html')
    html = template.render(context)
    pdf = html_to_pdf(html)
    
    if pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{name}_{resume.job_title}_resume.pdf"'
        return response
    else:
        return HttpResponse("Error Rendering PDF", status=400)
    
def generate_resume_prompt(job_title, job_description, existing_resume_text):
    prompt = f"""
        Rewrite this resume: ({existing_resume_text}) to fit a ({job_title}) position based on the job description: ({job_description})

        Requirements:
        - Emphasize relevant skills and experiences for the ({job_title}) role
        - Downplay or remove irrelevant skills and experiences
        - Highlight achievements demonstrating transferable skills
        - Include keywords from the job posting
        - List all relevant job responsibilities

        Guidance:
        - Begin bullets with action verbs (e.g., "managed", "created")
        - Quantify achievements with numbers and metrics where possible
        - Use industry-specific keywords and phrases

        JSON return format:
                {{
                    "name": "Full Name",
                    "contactDetails": {{
                        "email": "email@example.com",
                        "phone": "123-456-7890",
                        "linkedIn": "linkedin.com/in/username"
                    }},
                    "summary": "Professional summary",
                    "experience": [
                        {{
                            "title": "Job Title",
                            "company": "Company Name",
                            "dates": "Start Date - End Date",
                            "responsibilities": [
                                "Responsibility 1",
                                "Responsibility 2",
                                "Responsibility 3"
                            ]
                        }}
                    ],
                    "education": [
                        {{
                            "level": "Degree Type",
                            "school": "School Name",
                            "dates": "Graduation Date"
                        }}
                    ],
                    "skills": ["Skill 1", "Skill 2", "Skill 3"],
                    "interests": ["Interest 1", "Interest 2"],
                    "achievements": ["Achievement 1", "Achievement 2"]
                }}
        """
    return prompt

def generate_resume_text(prompt):
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are an assistant that ONLY speals JSON. Do not write normal text."
            },
            {
                "role": "user",
                "content": prompt
            },
        ],
        model="llama3-70b-8192",
    )
    print(chat_completion.choices[0].message.content)

    return chat_completion.choices[0].message.content


@login_required
def generate_resume(request):
    if request.method == "POST":
        # Get user inputs from the form
        job_title = request.POST.get("job_title")
        job_description = request.POST.get("job_description")
        existing_resume_txt = request.POST.get("existing_resume_text")
        existing_resume_file = request.FILES.get("existing_resume_file")

        if existing_resume_file:
            # Handle file upload case
            existing_resume_text = handle_file_upload(existing_resume_file)
            print(f"Existing resume text from file: {existing_resume_text}")

        else:
            # Handle pasted text case
            existing_resume_text = existing_resume_txt
            print(f"Existing resume text from form: {existing_resume_text}")

        # Generate the resume prompt
        prompt = generate_resume_prompt(job_title, job_description, existing_resume_text)

        # Call the Groq API to generate the resume
        generated_text = generate_resume_text(prompt)

        user = request.user
        if isinstance(user, CustomUser):
            generated_resume = GeneratedResume(
                user=user,
                job_title=job_title,
                job_description=job_description,
                existing_resume=existing_resume_text,
                generated_text=generated_text
            )
            generated_resume.save()

            return redirect('havard_resume', resume_id=generated_resume.id)
        else:
            pass

        context = {
            'resume_id': generated_resume.id,

        }
        print(f'***generated_resume:***', generated_resume)
        return redirect("havard_resume", context)

    return render(request, "generate_resume_form.html")

@login_required
def regenerate_resume(request, resume_id):
    # Get the existing resume object
    generated_resume = get_object_or_404(GeneratedResume, id=resume_id, user=request.user)

    if request.method == "POST":
        # Get user inputs from the form
        job_title = request.POST.get("job_title", generated_resume.job_title)
        job_description = request.POST.get("job_description", generated_resume.job_description)
        existing_resume_text = request.POST.get("existing_resume_text", generated_resume.existing_resume)

        # Generate the resume prompt
        prompt = generate_resume_prompt(job_title, job_description, existing_resume_text)

        # Call the API to generate the new resume text
        new_generated_text = generate_resume_text(prompt)

        # Update the existing GeneratedResume object
        generated_resume.job_title = job_title
        generated_resume.job_description = job_description
        generated_resume.existing_resume = existing_resume_text
        generated_resume.generated_text = new_generated_text
        generated_resume.save()

        return redirect('havard_resume', resume_id=generated_resume.id)

    # If it's a GET request, render a form pre-filled with existing data
    context = {
        'resume': generated_resume,
    }
    return render(request, "regenerate_resume_form.html", context)

def handle_file_upload(existing_resume_file):
    file_name = existing_resume_file.name
    existing_resume_text = ""

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

        blob_client.delete_blob()

    return existing_resume_text

@login_required
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

@login_required
def havard_resume(request, resume_id):
    resume = get_object_or_404(GeneratedResume, id=resume_id)
    
    try:
        generated_text = json.loads(resume.generated_text)
    except json.JSONDecodeError:
        generated_text = {} 
    
    context = {
        'resume': resume,
        'generated_text': generated_text,
        'resume_id': resume_id,
    }
    
    print(context)
    return render(request, 'havard_resume.html', context)

@login_required
def generate_cover_letter(request, resume_id):
    # Retrieve the generated resume
    generated_resume = get_object_or_404(GeneratedResume, id=resume_id)

    cover_letter_prompt = f"""
        Task: Write a humanly creative cover letter using this resume:({generated_resume.generated_text}) and this job description: ({generated_resume.job_description})

        Instructions:
        - Format the cover letter in HTML with paragraph tags (<p>).
        - Include a salutation and closing.
        
        Example Format:

        <p>Dear Hiring Manager,</p>

        <p>I am writing to express my interest in the [Job Title] position at [Company Name] as advertised. With a strong background in [Relevant Skill/Experience], I am excited about the opportunity to contribute to your team.</p>

        <p>In my previous role at [Previous Company], I successfully [Key Achievement or Responsibility]. This experience has equipped me with the skills to [Relevant Skill or Task].</p>

        <p>Moreover, I have [Additional Qualification or Experience], which aligns well with the requirements outlined in the job description.</p>

        <p>I am enthusiastic about the prospect of bringing my expertise to [Company Name] and am confident that my background and skills will make a valuable contribution to your team.</p>

        <p>Thank you for considering my application. I look forward to the opportunity to discuss how my skills and experiences align with the needs of your team.</p>

        <p>Sincerely,<br>
         Name</p>

        Note: You only Return the data as a properly formatted HTML resume. Do not write normal text.
        """
    # Generate cover letter from the resume text
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-1106",
            messages=[
            {"role": "system", "content": "You are an assistant that ONLY speals HTML. Do not write normal text."},
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
    print(generated_cover_letter_text)

    # Redirect to a page to display or download the generated cover letter
    return redirect('cover_letter_display', cover_letter_id=generated_cover_letter.id)

    
def cover_letter_display(request, cover_letter_id):
    cover_letter = get_object_or_404(GeneratedCoverLetter, id=cover_letter_id)         
    return render(request, 'cover_letter_display.html', {'cover_letter': cover_letter})

@login_required
def download_cover_letter(request, cover_letter_id):
    cover_letter = get_object_or_404(GeneratedCoverLetter, id=cover_letter_id)
    
    # Ensure the user has permission to access this cover letter
    if cover_letter.user != request.user:
        return HttpResponse("Access Denied", status=403)

    context = {
        'cover_letter': cover_letter,
    }

    # Get the associated resume and job title
    resume = cover_letter.generated_resume
    job_title = resume.job_title if resume else "Job"

    # Get the name from the associated resume's generated_text
    try:
        resume_generated_text = json.loads(resume.generated_text) if resume else {}
        name = resume_generated_text.get('name', 'Applicant')
    except json.JSONDecodeError:
        name = 'Applicant'

    template = get_template('cover_letter_pdf.html')
    html = template.render(context)
    pdf = html_to_pdf(html)
    
    if pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{name}_{job_title}_cover_letter.pdf"'
        return response
    else:
        return HttpResponse("Error Rendering PDF", status=400)

def user_resumes(request):
    # Get generated resumes for user 
    resumes = GeneratedResume.objects.filter(user=request.user)
    
    context = {
        'resumes': resumes        
    }
    return render(request, 'user_resumes.html', context)

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