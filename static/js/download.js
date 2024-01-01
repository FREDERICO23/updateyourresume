
function downloadPDF() {
    const { jsPDF } = window.jspdf;

    let doc = new jsPDF('p', 'px', [900, 900]);
    let pdfjs = document.querySelector('#resumeContainer');

    doc.html(pdfjs, {
        callback: function(doc) {
            doc.save("resume.pdf");
        },
        x: 12,
        y: 12
    });                
}            
