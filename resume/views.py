import openai
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404

from .models import GeneratedResume, GeneratedCoverLetter

import json
import fitz 
import docx
from .utils import render_to_pdf, render_to_word


CustomUser = get_user_model()
openai.api_key = ('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')

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import GeneratedResume

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

        Instructions:

        Input Data:

        Job Title: {job_title}
        Job Description: {job_description}
        Existing Resume: {existing_resume}
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
        return redirect("resume_display", context)  
    
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
    #return render_to_pdf('resume_display.html', context)

def save_resume(request):

    if request.method == 'POST':
        data = json.loads(request.body)
        updated_resume = data['resume']
        
        # Get Resume object for current user
        resume = get_object_or_404(GeneratedResume, user=request.user)
        
        # Update HTML field 
        resume.html_content = updated_resume  
        resume.save()
        
        return HttpResponse('Resume saved')

    return HttpResponseBadRequest()

def generate_cover_letter(request, resume_id):
    # Retrieve the generated resume
    generated_resume = get_object_or_404(GeneratedResume, id=resume_id)

    cover_letter_prompt = f"""
    Task: Generate a tailored cover letter based on the information extracted from the generated resume.

    Instructions:

    Generated Resume Text:
    {generated_resume.generated_text}

    Cover Letter Content:

    Introduction:

    Address the hiring manager or employer with a polite salutation.
    Express your interest in the position and briefly mention where you learned about the job opening.
    Highlight a key accomplishment or skill from your resume to capture attention.
    Body:

    Provide a brief overview of your professional background and experiences.
    Emphasize how your skills and experiences align with the requirements of the job.
    Reference specific achievements or projects mentioned in the resume.
    Express enthusiasm for the opportunity and explain why you are a suitable candidate.
    Closing:

    Express appreciation for considering your application.
    Mention your eagerness to further discuss your qualifications in an interview.
    Include a polite closing statement and express anticipation for a positive response.
    Note: Use the generated resume text to tailor the cover letter content, ensuring a cohesive and compelling narrative that aligns with the specific job requirements.

    Output:

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

def dashboard(request):
    return render(request, 'dashboard.html')

def genresume(request):
    return render(request, 'generate_resume.html')