
from io import BytesIO
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    SimpleDocTemplate,
    Paragraph,
    Spacer
)
from reportlab.lib.styles import getSampleStyleSheet

from bs4 import BeautifulSoup
from reportlab.platypus import Paragraph
from bs4 import BeautifulSoup

class PdfExporter:
    @staticmethod
    def export(chat_history):
        
        pdf_buffer=BytesIO()
        
        doc=SimpleDocTemplate(pdf_buffer)
        
        styles = getSampleStyleSheet()

        elements = []

        for item in chat_history:
            
            
            soup = BeautifulSoup(item["answer"], "html.parser")
            
            items=[]
            for s in soup.find_all('li'):
                text=s.get_text()
                items.append(ListItem(Paragraph(text, styles["BodyText"])))
            
            

            elements.append(
                        Paragraph(
                            f"Question: {item['question']}",
                            styles["Heading3"]
                        )
                    )
           
            elements.append(
                ListFlowable(items,bulletType='1'))
                                
                                
            elements.append(
                Spacer(1, 12)
            )

        doc.build(elements)

        pdf_buffer.seek(0)

        # Return the PDF buffer containing the generated PDF content
       
        return pdf_buffer