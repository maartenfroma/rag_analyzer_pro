
import sys
from pathlib import Path

# Set up the root directory for the project and add it to the system path
ROOT_DIR = Path(__file__).resolve().parents[2]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
import os



from rag_components.ai_assistants.gemini_ai_assistant import GeminiAssistant
from rag_components.core.rag_engine import RAGEngine
from rag_components.factories.processor_factory import ProcessorFactory
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

#
st.set_page_config(page_title="RAG Analyze Pro", layout="wide")

#
st.title("RAG Analyze Pro")


# Retrieve the Google API key from environment variables
api_key = os.getenv("GOOGLE_API_KEY")   
if not api_key:
    raise KeyError("Google API key is not set.")

# File uploader for various document and media types
uploaded_files = st.file_uploader("Choose files", [".pdf", ".docx", ".csv",
                                                   ".xlsx", ".mp3", ".wav", 
                                                   ".pptx", ".mp4"],
                                                   accept_multiple_files=True)

processors=[]

# Check if any files have been uploaded and process them accordingly
for uploaded_file in uploaded_files:
    extensions = "." + uploaded_file.name.split(".")[-1].lower()


    try:
        processors.append(ProcessorFactory.
                         create_processor(file_bytes=uploaded_file.read(), 
                                        file_name=uploaded_file.name, 
                                        api_key=api_key))
    except ValueError as e:
        st.error(str(e))


# Process the uploaded file using the appropriate processors
if processors and len(processors) > 0:

    current_files = tuple(f.name for f in uploaded_files)

    if (
        "current_file" not in st.session_state
        or st.session_state["current_file"] not in current_files
    ):

        with st.spinner("Document is being processed..."):

            st.write(f"PROCESSING: {current_files[0]}")

            # Initialize the Gemini assistant and RAG engine
            assistant = GeminiAssistant()

            # Create the RAG engine with the assistant
            st.session_state["rag_engine"] = RAGEngine(assistant=assistant)

            # Load the processors into the RAG engine and get the documents and chunks
            docs, chunks = st.session_state["rag_engine"].load_processors(processors)

            # Store the current file, documents, and chunks in the session state
            st.session_state["current_file"] = current_files[0]
            st.session_state["docs"] = docs
            st.session_state["chunks"] = chunks
            st.success("Document processed successfully!")

# Display the RAG engine interface if it has been initialized
if "rag_engine" in st.session_state:

    question = st.text_input("Ask a question to the RAG engine:")

else:
    st.warning("Please upload a file to initialize the RAG engine.")

# Submit the question to the RAG engine when the button is clicked
if st.button("Submit Question"):
        if question:
            with st.spinner("Getting answer from RAG engine..."):

                # Ask the RAG engine the question and get the answer and sources
                answer, sources = st.session_state["rag_engine"].ask(question, k=3)

                
                chat_history = st.session_state["rag_engine"].get_chat_history()

                for entry in chat_history:
                    with st.chat_message("user"):
                        st.write(f"Question: {entry['query']}")
                    with st.chat_message("assistant"):
                        st.write(f"Answer: {entry['response']}")

                # Display the chat history below the answer and sources
                st.subheader("Chat History")
                for i, entry in enumerate(chat_history, start=1):
                    st.write(f"Question{i}: {entry['query']}")
                    st.write(f"Answer{i}: {entry['response']}")

                # Button to clear the chat history
                if st.button("Clear Chat History"):
                    st.session_state["rag_engine"].clear_chat_history()
                    st.experimental_rerun()

 
                



