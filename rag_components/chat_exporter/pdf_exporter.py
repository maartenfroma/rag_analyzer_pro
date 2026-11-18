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

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Table, TableStyle

from reportlab.platypus import (
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

from reportlab.pdfgen import canvas

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
        
        styles.add(
            ParagraphStyle(
                name="ReportTitle",
                parent=styles["Title"],
                fontSize=26,
                leading=30,
                textColor=colors.HexColor("#1E3A8A"),
                spaceAfter=25,
            )
        )

        styles.add(
            ParagraphStyle(
                name="SectionHeader",
                parent=styles["Heading2"],
                fontSize=16,
                leading=20,
                textColor=colors.HexColor("#334155"),
                spaceBefore=12,
                spaceAfter=10,
            )
        )

        styles.add(
            ParagraphStyle(
                name="CustomBody",
                parent=styles["BodyText"],
                fontSize=10,
                leading=14,
            )
        )
                
        # Initialize the list of elements to be added to the PDF document
        elements = []
        
        elements.append(
            Paragraph(
                "RAG Analyzer Pro",
                styles["ReportTitle"]
            )
                )

        elements.append(
            Paragraph(
                "Enterprise AI Document Intelligence Report",
                styles["SectionHeader"]
            )
        )

        elements.append(
            Spacer(1, 30)
        )

        metadata_table = Table([
                ["Generated", f"{datetime.now():%d-%m-%Y %H:%M}"],
                ["Document", doc_title or "N/A"],
                ["Chunks Indexed", str(chunk_count or 0)],
                ["Questions", str(len(chat_history))],
                ["File Size",
                f"{round(file_size / (1024 * 1024), 2) if file_size else 0} MB"],
            ], colWidths=[140, 300])
        
        metadata_table.setStyle(
                            TableStyle([
                                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#E2E8F0")),
                                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                                ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                                ("ROWBACKGROUNDS", (1, 0), (-1, -1),
                                [colors.white, colors.HexColor("#F8FAFC")]),
                            ])
                        )

        elements.append(metadata_table)
        
        elements.append(
            Spacer(1, 20)
        )

        elements.append(
                Paragraph(
                    "Executive Summary",
                    styles["SectionHeader"]
                )
            )

        elements.append(
            Paragraph(
                f"""
                This report was generated using RAG Analyzer Pro and
                contains AI-generated insights based on indexed
                document content and semantic search retrieval.

                Total questions analysed: {len(chat_history)}
                Total chunks indexed: {chunk_count or 0}
                """,
                styles["CustomBody"]
            )
        )

        elements.append(
            Spacer(1, 20)
        )

        elements.append(
            Paragraph(
                "Analysis Results",
                styles["SectionHeader"]
            )
        )

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
    

        
                
            elements.append(Paragraph( "Question", styles["SectionHeader"]))
                                                         
                
            elements.append(
                    Paragraph(
                        html.escape(str(question)),
                        styles["CustomBody"]
                    )
                )
                
           

            elements.append(
                    Spacer(1, 6)
                )



            if answer:
                
                elements.append(
                        Paragraph(
                            "Answer",
                            styles["SectionHeader"]))
                   
                # Zet Markdown-antwoord van Gemini om naar HTML voor BeautifulSoup
                html_answer = markdown.markdown(str(answer))
                soup = BeautifulSoup(html_answer, "html.parser")


                for tag in soup.find_all(["h1", "h2", "h3", "p", "li"]):
                    
                    text = html.escape(
                                    tag.get_text(" ", strip=True)
                                )

                    if not text:
                            continue
                        
                    if tag.name == "h1":

                        elements.append(
                            Paragraph(
                                text,
                                styles["ReportTitle"]
                            )
                        )

                    elif tag.name == "h2":

                        elements.append(
                            Paragraph(
                                text,
                                styles["SectionHeader"]
                            )
                        )

                    elif tag.name == "h3":

                        elements.append(
                            Paragraph(
                                text,
                                styles["Heading3"]
                            )
                        )

                    elif tag.name == "li":

                        elements.append(
                            Paragraph(
                                f"• {text}",
                                styles["CustomBody"]
                            )
                        )

                    elif tag.name == "p":

                        elements.append(
                            Paragraph(
                                text,
                                styles["CustomBody"]
                            )
                        )

                    elements.append(
                        Spacer(1, 4)
                    )
                    

        doc.build(elements, onFirstPage=PdfExporter.add_page_number, onLaterPages=PdfExporter.add_page_number)
        pdf_buffer.seek(0)
        
        #Return the PDF buffer containing the generated PDF document
        return pdf_buffer
    
    @staticmethod
    def add_page_number(canvas, doc):
        page_num = canvas.getPageNumber()
        canvas.setFont("Helvetica", 9)

        canvas.drawRightString(
            550,
            20,
            f"Page {page_num}"
        )