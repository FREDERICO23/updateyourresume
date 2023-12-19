import io
from django.http import HttpResponse
from django.template.loader import get_template 
from xhtml2pdf import pisa
import docx
import PyPDF2
import fitz


# def extract_text_from_pdf(pdf_file):
#     """Extract text from a PDF file.
#     Args:
#         pdf_file (str): Path to the PDF file
#     Returns:
#         str: Extracted text from the PDF 
#     """
#     text = ""
#     with open(pdf_file, 'rb') as f:
#         pdf = PyPDF2.PdfReader(f)
#         for page in pdf.pages:
#             text += page.extract_text()
#     return text

def extract_text_from_pdf(azure_path):
    """Extract text from a PDF stored in Azure blob storage
    
    Args:
        azure_url (str): The URL of the PDF blob
        
    Returns:
        str: Extracted text string from PDF
    """
    try:
        doc = fitz.open(azure_path)
    except fitz.fitz.FileNotFoundError as err:
        print("FITZ ERROR:",err)
    
    doc = fitz.open(azure_path)
    text = ""
    
    for page in doc:
        text += page.getText()
        
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