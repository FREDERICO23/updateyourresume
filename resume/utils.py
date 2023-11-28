import io
from django.http import HttpResponse
from django.template.loader import get_template 
from xhtml2pdf import pisa
import docx

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