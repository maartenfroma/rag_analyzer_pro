
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
import os



from rag_components.ai_assistants.gemini_ai_assistant import GeminiAssistant
from rag_components.core.rag_engine import RAGEngine
from rag_components.processors.documents.pdf_processor import PdfProcessor
from rag_components.processors.documents.docx_processor import DocxProcessor
from rag_components.processors.documents.csv_processor import CsvProcessor
from rag_components.processors.documents.excel_processor import ExcelProcessor
from rag_components.processors.documents.pptx_processor import PPTXProcessor
from rag_components.processors.media.audio_processor import AudioProcessor
from rag_components.processors.media.video_processor import VideoProcessor
from dotenv import load_dotenv


load_dotenv()

st.set_page_config(page_title="RAG Analyze Pro", layout="wide")

st.title("RAG Analyze Pro")


# Retrieve the Google API key from environment variables
api_key = os.getenv("GOOGLE_API_KEY")   
if not api_key:
    raise KeyError("Google API key is not set.")

# Initialize the GeminiAssistant and RAGEngine
assistant = GeminiAssistant()
rag_engine = RAGEngine(assistant=assistant)

# File uploader for various document and media types
uploaded_file = st.file_uploader("Choose files", [".pdf", ".docx", ".csv",
                                                   ".xlsx", ".mp3", ".wav", 
                                                   ".pptx", ".mp4"])

if uploaded_file:
    extensions = "." + uploaded_file.name.split(".")[-1].lower()

    file_bytes = uploaded_file.read()

    processor=None

    if extensions == ".pdf":
        processor = PdfProcessor(file_bytes=file_bytes, api_key=api_key)
    elif extensions == ".docx":
        processor = DocxProcessor(file_bytes=file_bytes, api_key=api_key)
    elif extensions == ".csv":
        processor = CsvProcessor(file_bytes=file_bytes, api_key=api_key)
    elif extensions == ".xlsx":
        processor = ExcelProcessor(file_bytes=file_bytes, api_key=api_key)
    elif extensions in [".mp3", ".wav"]:
        processor = AudioProcessor(file_bytes=file_bytes, api_key=api_key)
    elif extensions == ".pptx":
        processor = PPTXProcessor(file_bytes=file_bytes, api_key=api_key)
    elif extensions == ".mp4":
        processor = VideoProcessor(file_bytes=file_bytes, api_key=api_key)

    # Process the uploaded file using the appropriate processor
    if processor:
        with st.spinner("Document is being processed..."):

            # Initialize a new GeminiAssistant and RAGEngine for processing the file    
            assistant=GeminiAssistant()
            engine = RAGEngine(assistant=assistant)
            docs, chunks = (engine.load_processor(processor))

            st.success("Document processed successfully!")
            st.write("Documents:", docs)
            st.write("Chunks:", chunks) 

            #
            st.session_state["rag_engine"] = engine 

            if "rag_engine" in st.session_state:
                question = st.text_input("Ask a question to the RAG engine:")

                if st.button("Submit Question"):
                    if question:
                        with st.spinner("Getting answer from RAG engine..."):
                            answer, sources = st.session_state["rag_engine"].ask(question)

                            st.subheader("Answer")
                            st.write(answer)
                            st.subheader("Sources")
                            st.write(sources)


                



