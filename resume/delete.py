import openai
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404

from .models import GeneratedResume, GeneratedCoverLetter

import json
import fitz 
import docx

CustomUser = get_user_model()
openai.api_key = ('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')

def extract_text_from_pdf(pdf_file):
    text = ""
    pdf_document = fitz.open(pdf_file)    
    for page_num in range(pdf_document.page_count):
        page = pdf_document[page_num]
        text += page.get_text()

    return text


def extract_text_from_docx(docx_file):
    text = ""
    doc = docx.Document(docx_file)
    for paragraph in doc.paragraphs:
        text += paragraph.text
    return text


def generate_resume(request):
    if request.method == "POST":
        # Get user inputs from the form
        job_title = request.POST.get("job_title")
        job_description = request.POST.get("job_description")
        existing_resume = request.POST.get("existing_resume_text")
        existing_resume_file = request.FILES.get("existing_resume_file")

        # If an existing resume file is uploaded, read the content
        if existing_resume_file:
            if existing_resume_file.name.endswith('.pdf'):
                existing_resume_text = extract_text_from_pdf(existing_resume_file)
            elif existing_resume_file.name.endswith('.docx'):
                existing_resume_text = extract_text_from_docx(existing_resume_file)
            else:
                existing_resume_text = existing_resume_text

        # Create a prompt for expert resume revamp
        prompt = f"""
        Task: Generate a professionally styled, ATS-compliant resume tailored to the provided job title, job description, and the existing resume. The aim is to optimize the resume to increase its compatibility with ATS systems, while creatively adjusting certain sections to better align with the job requirements.

        Job Title: {job_title}
        Job Description: {job_description}
        Existing Resume: {existing_resume}        
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
            resume_id = generated_resume.id  
            print(resume_id)
        else: 
            pass 
        
        context = {
            'resume': generated_text,
            'resume_id' :resume_id
        }

        return redirect("resume_display", context )  
    
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

def generate_cover_letter(request, resume_id):
    # Retrieve the generated resume
    generated_resume = get_object_or_404(GeneratedResume, id=resume_id)

    cover_letter_prompt = f"""
    Task: Generate a tailored cover letter based on the information extracted from the generated resume.    
    Generated Resume Text:
    {generated_resume.generated_text}
    Generate a well-crafted cover letter that complements the information in the generated resume.
    Ensure the cover letter is professionally written, error-free, and suitable for submission with job applications.
    """

    if request.method == "POST":
        # Generate cover letter from the resume text
        response = openai.Completion.create(
            model="gpt-3.5-turbo-1106",
            prompt= cover_letter_prompt,
            max_tokens=750,  # Adjust based on your requirements
            n=1  # Number of completions
        )

        generated_cover_letter_text = response.choices[0].text

        # Store the generated cover letter in the database
        generated_cover_letter = GeneratedCoverLetter(
            user=request.user,  # Assuming the user is authenticated
            generated_resume=generated_resume,
            generated_text=generated_cover_letter_text
        )
        generated_cover_letter.save()

        # Redirect to a page to display or download the generated cover letter
        return redirect('cover_letter_display', cover_letter_id=generated_cover_letter.id)

    # Render the template with the generated resume details
    return render(request, 'generate_cover_letter.html', {'generated_resume': generated_resume})

def cover_letter_display(request, cover_letter_id):
    cover_letter = get_object_or_404(GeneratedCoverLetter, id=cover_letter_id)
    
    if request.method == 'POST':
        # Handle download request
        response = HttpResponse(cover_letter.generated_text, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename=generated_resume.pdf'
        return response
    
    return render(request, 'cover_letter_display.html', {'cover_letter': cover_letter})

def display(request):
    return render(request, 'base.html')

def home(request):
    return render(request, 'pages/index.html')
def genresume(request):
    return render(request, 'generate_resume.html')