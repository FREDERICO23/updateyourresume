import io
from django.http import HttpResponse
from django.template.loader import get_template 
from xhtml2pdf import pisa
import docx
import PyPDF2
import fitz
from io import BytesIO
from azure.storage.blob import BlobServiceClient
import azure.storage.blob as azureblob
from django.conf import settings


def extract_text_from_pdf(azure_path, file_name):
    """Extract text from a PDF stored in Azure blob storage
    
    Args:
        azure_url (str): The URL of the PDF blob
        
    Returns:
        str: Extracted text string from PDF
    """
    blob_service = BlobServiceClient.from_connection_string(settings.AZURE_STORAGE_CONNECTION_STRING) 
    blob_client = blob_service.get_blob_client(settings.AZURE_STORAGE_CONTAINER, file_name) 
    # Download blob contents to bytes 
    downloaded_bytes = BytesIO()
    blob_client.download_blob().download_to_stream(downloaded_bytes)

    # Extract text from bytes 
    downloaded_bytes.seek(0) # Rewind pointer to start 
    try:
        doc = fitz.open("pdf", downloaded_bytes) 
    except fitz.fitz.FileNotFoundError as err:
        print("FITZ ERROR:",err)
    
    doc = fitz.open("pdf", downloaded_bytes) 
    text = ""    
    for page in doc:
        text += page.get_textpage().extractText()       
    return text

def extract_text_from_docx(docx_file):
    """Extract text from a DOCX file.
    Args:
        docx_file (str): Path to the DOCX file
    Returns:
        str: Extracted text from the DOCX 
    """
    doc = docx.Document(docx_file)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return '\n'.join(full_text)

def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html  = template.render(context_dict)
    result = io.BytesIO()

    # Create the PDF using xhtml2pdf
    pdf = pisa.pisaDocument(io.BytesIO(html.encode("ISO-8859-1")), result)
    
    if pdf.err:
        return HttpResponse("Invalid PDF", status_code=400, content_type='text/plain')
    return HttpResponse(result.getvalue(), content_type='application/pdf')



def render_to_word(template_src, context_dict={}):
    template = get_template(template_src)
    html = template.render(context_dict)
    
    word_file = io.BytesIO()
    document = docx.Document()
    document.add_heading('Report', 0)
    
    document.add_paragraph(html)
    document.save(word_file)
            
    word_file.seek(0) 

    response = HttpResponse(word_file.read(), content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    response['Content-Disposition'] = 'attachment; filename=report.docx'
            
    return response