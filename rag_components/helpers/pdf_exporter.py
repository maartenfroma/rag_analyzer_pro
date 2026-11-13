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


class PdfExporter:

    @staticmethod
    def export(chat_history):
        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(pdf_buffer)
        styles = getSampleStyleSheet()
        elements = []

        for entry in chat_history:
            if not isinstance(entry, dict):
                continue

            # Gebruik de juiste keys uit je RAG-engine ('query' en 'response')
            question = entry.get("query", "")
            answer = entry.get("response", "")

            if question:
                elements.append(
                    Paragraph(
                        f"Question: {html.escape(str(question))}",
                        styles["Heading3"],
                    )
                )

            if answer:
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
                    elements.append(ListFlowable(items, bulletType="1"))
                else:
                    for p in soup.find_all("p"):
                        text = html.escape(p.get_text(strip=True))
                        if text:
                            elements.append(Paragraph(text, styles["BodyText"]))
                            elements.append(Spacer(1, 6))

            elements.append(Spacer(1, 12))

        doc.build(elements)
        pdf_buffer.seek(0)
        return pdf_buffer