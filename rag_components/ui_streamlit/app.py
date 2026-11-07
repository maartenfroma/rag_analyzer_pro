import streamlit as st
import os
from ai_assistants.gemini_ai_assistant import GeminiAssistant
from rag_components.core.rag_engine import RAGEngine
from rag_components.processors.documents.pdf_processor import PdfProcessor
from rag_components.processors.documents.docx_processor import DocxProcessor
from rag_components.processors.documents.csv_processor import CsvProcessor
from rag_components.processors.documents.excel_processor import ExcelProcessor
from rag_components.processors.documents.pptx_processor import PPTXProcessor
from rag_components.processors.media.audio_processor import AudioProcessor
from rag_components.processors.media.video_processor import VideoProcessor


st.set_page_config(page_title="RAG Analyze Pro", layout="wide")

st.title("RAG Analyze Pro")

# Initialize the GeminiAssistant and RAGEngine
assistant = GeminiAssistant()
rag_engine = RAGEngine(assistant=assistant)


# Retrieve the Google API key from Streamlit secrets or environment variables
api_key = st.secrets.get(
    "GOOGLE_API_KEY",
    os.getenv("GOOGLE_API_KEY")
)

if not api_key:
    st.error("Google API key is not set. Please provide it in Streamlit secrets or environment variables.") 
    st.stop()

# File uploader for various document and media types
uploaded_file = st.file_uploader("Choose files", [".pdf", ".docx", ".csv", ".txt",
                                                   ".xlsx", ".mp3", ".wav", 
                                                   ".pptx", ".mp4"])

if uploaded_file:
    extensions = "." + uploaded_file.name.split(".")[-1].lower()

    file_bytes = uploaded_file.read()

    processor=None

    if extensions == ".pdf":
        processor = PdfProcessor()
    elif extensions == ".docx":
        processor = DocxProcessor()
    elif extensions == ".csv":
        processor = CsvProcessor()
    elif extensions == ".xlsx":
        processor = ExcelProcessor()
    elif extensions in [".mp3", ".wav"]:
        processor = AudioProcessor()
    elif extensions == ".pptx":
        processor = PPTXProcessor()
    elif extensions == ".mp4":
        processor = VideoProcessor()

    if processor:
        processor.process(file_bytes)
    else:
        st.error(f"Unsupported file type: {extensions}")


