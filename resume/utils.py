import io
from django.http import HttpResponse
from django.template.loader import get_template 
import docx
import PyPDF2
import fitz
from io import BytesIO
from azure.storage.blob import BlobServiceClient
import azure.storage.blob as azureblob
from django.conf import settings
from docx import Document

from django.http import HttpResponse
from django.template.loader import get_template

from xhtml2pdf.document import pisaDocument
from xhtml2pdf import pisa

def html_to_pdf(html_content):
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html_content.encode("UTF-8")), result)
    if not pdf.err:
        return result.getvalue()
    return None


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


def extract_text_from_docx(file_name):
    """Extract text from a Word document stored in Azure blob storage
    
    Args:
        file_name (str): The name of the Word document in the blob storage
        
    Returns:
        str: Extracted text string from Word document
    """
    blob_service = BlobServiceClient.from_connection_string(settings.AZURE_STORAGE_CONNECTION_STRING) 
    blob_client = blob_service.get_blob_client(settings.AZURE_STORAGE_CONTAINER, file_name) 
    
    # Download blob contents to bytes 
    downloaded_bytes = BytesIO()
    blob_client.download_blob().download_to_stream(downloaded_bytes)

    # Extract text from bytes 
    downloaded_bytes.seek(0) # Rewind pointer to start 
    try:
        doc = Document(downloaded_bytes)
    except Exception as err:
        print("DOCX ERROR:", err)
        return ""

    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
        
    return text


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