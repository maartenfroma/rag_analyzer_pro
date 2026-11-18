from io import BytesIO
import html
import markdown
from bs4 import BeautifulSoup
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

from datetime import datetime   

# PDF Exporter class for exporting chat history to a PDF file
# This class provides functionality to export chat history to a PDF file using ReportLab.
class PdfExporter:

    # Export the given chat history to a PDF file
    # Creates docs from elements and returns the PDF buffer containing the generated PDF document
    
    @staticmethod
    def export(chat_history, doc_title=None, chunk_count=None, file_size=None):
        
        # chat_history is expected to be a list of dictionaries with 'query' and 'response' keys
        pdf_buffer = BytesIO()
        
        # Create a PDF buffer to store the generated PDF content
        doc = SimpleDocTemplate(pdf_buffer)
        
        # Initialize the PDF document with the buffer as the output destination
        styles = getSampleStyleSheet()
        
        # Initialize the list of elements to be added to the PDF document
        elements = []
        
        # Add the title and header information to the PDF elements
        elements.append(
            Paragraph(
                doc_title or "RAG Analyzer Pro",
                styles["Title"]
            )
        )

        # Add a spacer after the header information
        elements.append(
            Paragraph(
                "AI-Powered Document Analysis",
                styles["Heading2"]
            )
        )

        # Add the generation timestamp to the PDF elements
        elements.append(
            Paragraph(
                f"Generated: {datetime.now():%d-%m-%Y %H:%M}",
                styles["Normal"]
            )
        )
        
        if doc_title:
            
            elements.append(
                Paragraph(
                    f"Document: {html.escape(str(doc_title))}",
                    styles["Normal"]
                )
            )
            
        if chunk_count is not None:
            elements.append(
                Paragraph(
                    f"Chunk Count: {chunk_count}",
                    styles["Normal"]
                )
            )
        if file_size is not None:
            elements.append(
                Paragraph(
                     f"File Size: {round(file_size / (1024 * 1024), 2)} MB",
                    styles["Normal"]
                )
            )
            
        elements.append( Paragraph(f"Questions Analyzed: {len(chat_history)}",
                                            styles["Normal"]))
                               
                           
        elements.append(
            Spacer(1, 20)
        )

        # Iterate over each entry in the chat history and add it to the PDF elements
        for entry in chat_history:
            if not isinstance(entry, dict):
                continue

            # Gebruik de juiste keys uit je RAG-engine ('query' en 'response')
            question = entry.get("query", "")
            answer = entry.get("response", "")
            metadata = entry.get("metadata", {})

            # Add the question to the PDF elements if it exists
            if question:
                if metadata:    
                    elements.append(
                        Paragraph(
                            f"Metadata: {html.escape(str(metadata))}",
                            styles["Normal"]
                        )
                    )
                
                elements.append(Paragraph( "Question", styles["Heading2"]))
                                                         
                
                elements.append(
                    Paragraph(
                        html.escape(str(question)),
                        styles["BodyText"]
                    )
                )
                
                if metadata:
                    elements.append(
                        Paragraph(
                            f"Metadata: {html.escape(str(metadata))}",
                            styles["Normal"]
                        )
                    )

                elements.append(
                    Spacer(1, 6)
                )



            if answer:
                
                elements.append(
                        Paragraph(
                            "Answer",
                            styles["Heading2"]))
                   
                # Zet Markdown-antwoord van Gemini om naar HTML voor BeautifulSoup
                html_answer = markdown.markdown(str(answer))
                soup = BeautifulSoup(html_answer, "html.parser")

                li_elements = soup.find_all("li")
                if li_elements:
                    items = [
                        ListItem(
                            Paragraph(
                                html.escape(li.get_text(strip=True)),
                                styles["BodyText"],
                            )
                        )
                        for li in li_elements
                    ]
                    elements.append(ListFlowable(items, bulletType="bullet"))
                else:
                    for p in soup.find_all("p"):
                        text = html.escape(p.get_text(strip=True))
                        if text:
                            elements.append(Paragraph(text, styles["BodyText"]))
                            elements.append(Spacer(1, 6))

        elements.append(Spacer(1,20))
        
        elements.append(Paragraph( "Generated by RAG Analyzer Pro",styles["Italic"]))

        doc.build(elements)
        pdf_buffer.seek(0)
        
        #Return the PDF buffer containing the generated PDF document
        return pdf_buffer