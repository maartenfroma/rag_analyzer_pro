
from datetime import datetime
from importlib.metadata import metadata
import sys
from pathlib import Path
import json



# Set up the root directory for the project and add it to the system path
ROOT_DIR = Path(__file__).resolve().parents[2]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
import os



from rag_components.ai_assistants.gemini_ai_assistant import GeminiAssistant
from rag_components.core.rag_engine import RAGEngine
from rag_components.factories.processor_factory import ProcessorFactory
from rag_components.helpers.meta_display_helper import MetaDisplayHelper
from rag_components.helpers.export_file_helper import ChatHistoryExporter
from rag_components.helpers.pdf_exporter import PdfExporter
from dotenv import load_dotenv

from io import BytesIO
import pandas as pd

# Load environment variables from the .env file
load_dotenv()

#
st.set_page_config(page_title="RAG Analyze Pro", layout="wide")

col1, col2 = st.columns([8,1])

with col1:
    st.title("RAG Analyze Pro")

with col2:
    if st.button("🔄 Reset"):
        st.session_state.clear()
        st.rerun()




# Retrieve the Google API key from environment variables
api_key = os.getenv("GOOGLE_API_KEY")   
if not api_key:
    raise KeyError("Google API key is not set.")

# File uploader for various document and media types
uploaded_files = st.file_uploader("Choose files", [".pdf", ".docx", ".csv",
                                                   ".xlsx", ".mp3", ".wav", 
                                                   ".pptx", ".mp4"],
                                                   accept_multiple_files=True)

print("CREATING PROCESSORS")
processors=[]

# Check if any files have been uploaded and process them accordingly
for uploaded_file in uploaded_files:


    try:
        processors.append(ProcessorFactory.
                         create_processor(file_bytes=uploaded_file.read(), 
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

            

            # Initialize the Gemini assistant and RAG engine
            assistant = GeminiAssistant()

            # Create the RAG engine with the assistant
            st.session_state["rag_engine"] = RAGEngine(assistant=assistant)

            print("LOADING PROCESSORS")

            # Load the processors into the RAG engine and get the documents and chunks
            docs, chunks = st.session_state["rag_engine"].load_processors(processors)

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
            
            # Export the chat history for the current question and answer
            ChatHistoryExporter.export(
                question=question,
                answer=answer,
                metadata=[doc.metadata for doc in st.session_state["rag_engine"].last_retrieved_docs]
            )

            
            with st.chat_message("assistant"):
                
                # Display the answer from the RAG engine
                st.write(answer)

                # Display the sources used for the answer
                st.write(f"📚 Sources Used ({len(st.session_state['rag_engine'].last_retrieved_docs)})")
            
                #
                
                for idx,doc in enumerate(st.session_state["rag_engine"].last_retrieved_docs,start=1):
                    
                    with st.expander("View Document Details"):
                    
                                            # Format and display the metadata for the document
                                            meta = MetaDisplayHelper.format(doc.metadata)
                                         
                                            st.json(doc.metadata)
                                            
                                               
                    
                                            st.caption(
                                                doc.page_content[:500] + "..."
                                            )
                    
                                            st.divider()



                 

else:

    st.warning(
        "Please upload a file to initialize the RAG engine."
    )
                       

current_filename="this_file"
if "rag_engine" in st.session_state:
    
    engine=st.session_state["rag_engine"]
    
    if hasattr(engine, "last_retrieved_docs") and engine.last_retrieved_docs:
        first_doc = engine.last_retrieved_docs[0]
        source = first_doc.metadata.get(f"file_name")
        current_file_name = "this_file"
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
        
        json_data=json.dumps(chat_history, indent=4,
                              ensure_ascii=False)
        
        col1, col2, col3= st.columns(3)
        
        # Export buttons for JSON, Excel, and PDF
        
        with col1:
            
            
            current_date = datetime.now().strftime("%Y-%m-%d")
            st.download_button(
                label="📋 Export JSON",
                data=json_data,
                file_name=f"chat_history_{current_file_name}_{current_date}.json",
                mime="application/json"
            )
        # Export Excel button
        with col2:
            
            
            current_date = datetime.now().strftime("%Y-%m-%d")

            excel_buffer = BytesIO()

            with pd.ExcelWriter(
                excel_buffer,
                engine="openpyxl"
            ) as writer:

                df.to_excel(
                    writer,
                    sheet_name="Chat History",
                    index=False
                )

            excel_buffer.seek(0)

            st.download_button(
                label="📊 Export Excel",
                data=excel_buffer,
                file_name=f"chat_history_{current_file_name}_{current_date}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
                        
        # Export PDF button
        with col3:
            
            # Get the current file name and date for the PDF file name
            current_file_name = st.session_state.get("current_file_name", "chat_history")
            current_date = datetime.now().strftime("%Y-%m-%d")
            
            # Generate the PDF using the chat history
            pdf=PdfExporter.export(chat_history)
            st.download_button(
                label="📄 Export PDF",
                data=pdf,
                file_name=f"chat_history_{current_file_name}_{current_date}.pdf",
                mime="application/pdf"
            )

    





