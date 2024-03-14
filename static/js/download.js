
// function downloadPDF() {
//     const { jsPDF } = window.jspdf;

//     let doc = new jsPDF('p', 'px', [900, 900]);
//     let pdfjs = document.querySelector('#resumeContainer');

//     doc.html(pdfjs, {
//         callback: function(doc) {
//             doc.save("resume.pdf");
//         },
//         x: 12,
//         y: 12
//     });                
// }            
function downloadPDF() {
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF('p', 'px', [900, 900]);
  
    const pdfjs = document.querySelector('#resumeContainer');
  
    html2canvas(pdfjs, {
      scale: 2, // Adjust scale to improve image quality
      useCORS: true,
      allowTaint: true,
      logging: true
    }).then(function(canvas) {
      const imgData = canvas.toDataURL('image/png', 1.0);
  
      const width = doc.internal.pageSize.getWidth();
      const height = doc.internal.pageSize.getHeight();
  
      doc.addImage(imgData, 'PNG', 0, 0, width, height);
  
      // Add text layer on top of the image while preserving styles
      const textData = doc.getTextData();
      for (let i = 0; i < textData.length; i++) {
        doc.setTextColor(textData[i].fontColor);
        doc.setFontSize(textData[i].fontSize);
        doc.setFontStyle(textData[i].fontStyle);
        doc.text(textData[i].str, textData[i].x, textData[i].y);
      }
  
      doc.save('resume.pdf');
    });
  }