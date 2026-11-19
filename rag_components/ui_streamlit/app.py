from io import BytesIO
import pandas as pd

import sys
from pathlib import Path
import json


# Set up the root directory for the project and add it to the system path
ROOT_DIR = Path(__file__).resolve().parents[2]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


from rag_components.models.doc_data_model import DocData
from rag_components.models.chat_data_model import ChatData
from rag_components.db_manager.chat_repository import ChatRepository
from rag_components.db_manager.document_repository import DocumentRepository
from datetime import datetime

from rag_components.ai_assistants.gemini_ai_assistant import GeminiAssistant
from rag_components.core.rag_engine import RAGEngine
from rag_components.factories.processor_factory import ProcessorFactory
from rag_components.chat_exporter.main_exporter import MainExporter

from rag_components.db_manager.table_manager import DBCreateTable

from rag_components.helpers.initialize_metrics_session import initialize_metrics_session

from dotenv import load_dotenv


import streamlit as st
import os


# Load environment variables from the .env file
load_dotenv()

# Maximum allowed file sizes for video and audio uploads in megabytes
MAX_VIDEO_SIZE_MB = 500
MAX_AUDIO_SIZE_MB = 300
MAX_VIDEO_DURATION_MINUTES = 90


#Set up the Streamlit page configuration and initialize the metrics session
st.set_page_config(page_title="RAG Analyzer Pro", layout="wide")

# Create necessary database tables if they do not exist
DBCreateTable.create_table_documents()
DBCreateTable.create_table_chat()
 
if "db_initialized" not in st.session_state:

    DocumentRepository.delete_all()
    ChatRepository.delete_all()

    st.session_state["db_initialized"] = True
    

# Initialize the metrics session at startup
initialize_metrics_session()


############################STYLING#######################################
##########################################################################


st.markdown("""
<style>

div[data-testid="stMetric"] {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 20px;
}

div[data-testid="stMetric"] label {
    color: white !important;
}

div[data-testid="stMetricValue"] {
    color: white !important;
}

div[data-testid="stMetricDelta"] {
    color: white !important;
}

</style>
""", unsafe_allow_html=True)


############################MAIN LAYOUT###################################



col1, col2 = st.columns([8,1])

with col1:
    
        st.title("RAG Analyzer Pro")

        st.caption(
              "Enterprise document intelligence powered by RAG, semantic search and Gemini AI."
        )

        st.info(
            "📂 Upload documents • 🔎 Analyze content • 🤖 Generate insights • 📤 Export reports"
           )

# Reset button functionality for the uploader and metrics session
with col2:
    
    if st.button("🔄 Reset"):
        uploader_key = st.session_state.get("uploader_key", 0) + 1
        
        # Clear the current session state to reset all metrics and uploader keys
        st.session_state.clear()
        
        # Delete all documents and chats from the repositories db   
        DocumentRepository.delete_all()
        ChatRepository.delete_all()
      
        # Preserve the uploader key after clearing the session state
        st.session_state["uploader_key"] = uploader_key
        
        # Reinitialize the metrics session after preserving the uploader key
        initialize_metrics_session()
        
        # Rerun the app to apply the reset and updated uploader key
        st.rerun()
    
            
get_docs=DocumentRepository.get_all()

get_chats=ChatRepository.get_all()

m1, m2, m3, m4 = st.columns(4)

with m1:
    st.metric(
        "📄 Documents",
        len(get_docs)
    )

with m2:
    st.metric(
        "💬 Questions",
        len(get_chats)
    )

with m3:
    st.metric(
        "📦 Chunks",
        f"{st.session_state.get('chunks', 0):,}"
    )

with m4:
    st.metric(
        "🤖 Model",
        "Gemini"
    )
    
st.divider()





# Retrieve the Google API key from environment variables
api_key = os.getenv("GOOGLE_API_KEY")   
if not api_key:
    raise KeyError("Google API key is not set.")

if "uploader_key" not in st.session_state:
    st.session_state["uploader_key"] = 0
    
# File uploader for various document and media types
uploaded_files = st.file_uploader("Choose files", [".pdf", ".docx", ".csv",
                                                   ".xlsx", ".mp3", ".wav", 
                                                   ".pptx", ".mp4"],
                                                   accept_multiple_files=True,
                                                   key=f"uploader_{st.session_state['uploader_key']}")


for uploaded_file in uploaded_files:

    file_size_mb = uploaded_file.size / (1024 * 1024)
    extension = Path(uploaded_file.name).suffix.lower()

    if extension == ".mp4" and file_size_mb > MAX_VIDEO_SIZE_MB:
        st.error(
            f"Video mag maximaal {MAX_VIDEO_SIZE_MB} MB zijn."
        )
        st.stop()

    if extension in [".mp3", ".wav"] and file_size_mb > MAX_AUDIO_SIZE_MB:
        st.error(
            f"Audio mag maximaal {MAX_AUDIO_SIZE_MB} MB zijn."
        )
        st.stop()
        
print("CREATING PROCESSORS")
processors=[]

# Check if any files have been uploaded and process them accordingly
for uploaded_file in uploaded_files:
    


    try:
        processors.append(ProcessorFactory.
                         create_processor(file_bytes=uploaded_file.getvalue(), 
                                        file_name=uploaded_file.name, 
                                        api_key=api_key))
    except ValueError as e:
        st.error(str(e))


# Process the uploaded file using the appropriate processors
if processors and len(processors) > 0:

    current_files = [f.name for f in uploaded_files]

    # Create a unique signature for the current set of uploaded files
    #This is for creating a unique signature to track the current set of uploaded files
    current_signature="|".join(current_files) 

    if (
       "current_signature" not in st.session_state
        or st.session_state["current_signature"] != current_signature
    ):

        with st.spinner("Documents are being processed..."):

            
            if "rag_engine" not in st.session_state:

                # Initialize the Gemini assistant and RAG engine
                assistant = GeminiAssistant()

                # Create the RAG engine with the assistant
                st.session_state["rag_engine"] = RAGEngine(assistant=assistant)

            print("LOADING PROCESSORS")

            # Load the processors into the RAG engine and get the documents and chunks
            docs, chunks = st.session_state["rag_engine"].load_processors(processors)
            st.session_state["chunks"] = chunks
            
            if uploaded_files:
                uploaded=uploaded_files[0]
                
            file_bytes=uploaded.getvalue()
            
            
            st.session_state["file_size"] = len(file_bytes)
            
            file_size = st.session_state["file_size"]
            
    
            doc=DocData(
                    file_name=uploaded.name,
                    file_size=file_size,
                    chunk_count=st.session_state.get("chunks", 0),
                    embedding_model=os.getenv("EMBEDDING_MODEL"),
                    status="processed"
                )
            
            save_doc=DocumentRepository.save(doc)
            
            
            # Store the current file, documents, and chunks in the session state
            st.session_state["current_signature"] = current_signature   
            st.session_state["docs"] = docs
            st.session_state["chunks"] = chunks
            st.success("Document processed successfully!")

# Display the RAG engine interface if it has been initialized
if "rag_engine" in st.session_state:

    question = st.text_input(
        "Ask a question to the RAG engine:"
    )

    search_mode = st.selectbox(
        "Analysis Mode",
        [
            "⚡ Fast",
            "⚖️ Balanced",
            "🔎 Deep Analysis"
        ],
        help="""
        Fast: snel antwoord
        Balanced: beste balans
        Deep Analysis: meer bronnen en context
        """
    )

    k_map = {
        "⚡ Fast": 3,
        "⚖️ Balanced": 10,
        "🔎 Deep Analysis": 20,
    }

    k = k_map.get(search_mode, 10)

    if st.button("Submit Question") and question:

        with st.spinner(
            "Getting answer from RAG engine..."
        ):

            #
            answer, sources = (
                st.session_state["rag_engine"]
                .ask(question, k=k)
            )
            
            # Create a new chat entry with the question, answer, and timestamp
            chat = ChatData(
                    question=question,
                    answer=answer,
                    created_at=datetime.now()
                )

            # Save the chat entry to the repository
            save_chat=ChatRepository.save(chat)
            
         
            with st.chat_message("assistant"):
                
                # Display the answer from the RAG engine
                st.write(answer)

            sources = st.session_state["rag_engine"].last_retrieved_docs

            with st.expander(
                f"📚 Sources Used ({len(sources)})"
            ):

                for idx, doc in enumerate(
                    sources[:5],
                    start=1
                ):

                    st.markdown(
                        f"### 📄 Source {idx}"
                    )

                    st.json(doc.metadata)

                    st.caption(
                        doc.page_content[:500] + "..."
                    )

                    st.divider()
                  
          

else:

    st.warning(
        "Please upload a file to initialize the RAG engine."
    )
                       

current_file_name="this_file"
if "rag_engine" in st.session_state:
    
    engine=st.session_state["rag_engine"]
    
    if hasattr(engine, "last_retrieved_docs") and engine.last_retrieved_docs:
        first_doc = engine.last_retrieved_docs[0]
        source = first_doc.metadata.get(f"file_name")
        current_file_name = st.session_state.get("current_file_name", "this_file")
        if source:
            current_file_name = (
                str(source).split("/")[-1].split("\\")[-1].rsplit(".", 1)[0]
            )
        st.session_state["current_file_name"] = current_file_name
        
    # Retrieve the chat history from the RAG engine
    chat_history = st.session_state["rag_engine"].get_chat_history()

    
    
    # Display the chat history in the chat interface
    for entry in chat_history:
        with st.chat_message("user"):
            st.write(entry['query'])
        with st.chat_message("assistant"):
            st.write(entry['response'])
            
    if chat_history:
        
        df=pd.DataFrame(chat_history)
        
        st.divider()
        
        st.subheader("📤 Export Chat History")
        
    
        format_map = {
            "📄 PDF": "pdf",
            "📊 Excel": "excel",
            "📋 JSON": "json",
            "📝 DOCX": "docx",
            "📑 CSV": "csv"
        }
        
        extension_map = {
            "pdf": "pdf",
            "excel": "xlsx",
            "json": "json",
            "docx": "docx",
            "csv": "csv"
        }
        
        export_format = st.selectbox(
            "📤 Export Format",
            list(format_map.keys())
                )
        
        selected_format = format_map[export_format]
        
         # Export the chat history for the current question and answer
        export_chat_history = MainExporter.export(
            format_map[export_format],
            chat_history=chat_history,
            doc_title=st.session_state.get("current_file_name"),
            chunk_count=st.session_state.get("chunks"),
            file_size=st.session_state.get("file_size")
        )
     

        
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        st.download_button(
            "Download",
            data=export_chat_history,
            file_name = (
            f"RAG_Analysis_"
            f"{len(uploaded_files)}_documents_"
            f"{current_date}"
                ) + f".{extension_map[selected_format]}" )  
        
        
       
    





