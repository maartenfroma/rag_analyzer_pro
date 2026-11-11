
import os
import tempfile
from pathlib import Path
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from faster_whisper import WhisperModel
from rag_components.processors.base.base_media_processor import BaseMediaProcessor

from rag_components.exceptions.document_exceptions import (
    DocumentLoadError, DocumentSplitError, 
    DocumentValidationError, DocumentSaveError)

from rag_components.helpers.metadata_helper import MetadataHelper

import traceback

# Audio processor for handling audio files, transcription, 
# and document creation    
class AudioProcessor(BaseMediaProcessor):

    # Initialize the audio processor with file bytes, API key, model size, and chunk settings
    # file_bytes: The audio file content in bytes
    # api_key: API key for Google Generative AI Embeddings
    # model_size: Size of the Whisper model to use for transcription
    # chunk_size: Size of text chunks for splitting the transcript
    # chunk_overlap: Overlap between text chunks

    def __init__(self, file_bytes: bytes, api_key:str, file_name: str, model_size="small", 
                 chunk_size=1000, chunk_overlap=200):

        # Initialize the audio processor and its attributes
        self.temp_file = None
        self.model = WhisperModel(model_size)
        self.transcript = None
        self.chunks = None
        self.vector_store = None    
        self.file_bytes = file_bytes
        self.file_name = file_name
        self.file_path = None
        self.api_key = api_key
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.documents = []
        self.DB_PATH = os.path.join(
                    "chroma_db",
                    Path(self.file_name).stem
                )
        self.segments=[]
        

    # Load the audio file from the given path or from the temporary file if no path is provided
    # file_path: Path to the audio file. If None, the temporary file will be used.

    def load_file(self, file_path=None):

        # Load the audio file into a temporary file for processing
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(self.file_name).suffix) as temp_file:
                temp_file.write(self.file_bytes)
                temp_file.flush()
                self.file_path = temp_file.name
            return self.file_path   
        except Exception as e:
            raise DocumentLoadError("Failed to load audio file.") from e
    
    # Transcribe the loaded audio file into text
    # Returns the transcript as a string
    # Raises ValueError if the file is not loaded or does not exist

    def transcribe(self):

        # Start the transcription process
        print("Starting transcription")

    # Transcribe the audio file using the Whisper model
        segments, _ = self.model.transcribe(
            self.file_path
        )
        # Store the transcription segments for further processing
        self.segments = list(segments)

        print(
            f"Segments found: {len(self.segments)}"
        )

        # Combine the transcription segments into a single transcript string    
        self.transcript = " ".join(
            segment.text
            for segment in self.segments
        )

        print("Transcript completed")

        return self.transcript

    # Split the transcript into chunks for further processing
    # Returns a list of text chunks
    # Raises ValueError if the transcript is not available

    def create_documents(self):

        # Ensure that the transcript is available before creating documents
        if not self.transcript:
            raise DocumentValidationError(
                "Transcript not available. Call transcribe() first."
            )

        # Initialize the list of documents to be created from the transcript
        self.documents = []

        # Create documents for each transcription segment
        for i, segment in enumerate(self.segments):
            metadata = MetadataHelper.build_metadata(
                source="audio",
                file_name=self.file_name,
                index=i,
                start_time=segment.start,
                end_time=segment.end,
                chunk_index=len(self.documents)
            )

            # Build the metadata for the current transcription segment
            self.documents.append(
                Document(
                    page_content=segment.text,
                    metadata=metadata
                )
            )

        # Return the list of created documents
        return self.documents

    # Split the created documents into smaller chunks for processing
    def split_documents(self):

        # Ensure that there are documents available to split
        if not self.documents:
            raise DocumentValidationError(
                 "No documents available."
                     )
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
            )

        # Split the documents into chunks using the text splitter
        self.chunks = text_splitter.split_documents(
        self.documents
         )

        # Return the list of chunks created from the documents
        return self.chunks
    


    # Create a vector store from the chunks for retrieval
    # Raises DocumentSplitError if no chunks are available
    # Returns the created vector store for retrieval
    def create_vector_store(self):

        # Ensure that there are chunks available before creating the vector store
        if not self.chunks:
            raise DocumentSplitError(
                "No chunks available. Call split_documents() first."
            )

        # Initialize the embeddings for the vector store
        embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=self.api_key,
        task_type="retrieval_document"
        )

        # Check if the database file already exists and load or create the vector store accordingly
        if os.path.exists(self.DB_PATH):
            print("Loading existing database file:", self.DB_PATH)
            self.vector_store = Chroma(
                persist_directory=self.DB_PATH,
                embedding_function=embeddings,
            )
        else:
            print("Creating new database file:", self.DB_PATH)
            self.vector_store = Chroma.from_documents(
                documents=self.chunks,
                embedding=embeddings,
                persist_directory=self.DB_PATH
            )

        # Return the created vector store for retrieval 
        return self.vector_store

    
    # Process the audio file through all steps: load, transcribe, create documents, split, and create vector store
    # Returns the vector store, number of documents, and number of chunks if successful
    # Handles and prints errors for each processing step    
    def process(self):

        try:
            os.environ["GOOGLE_API_KEY"] = self.api_key

            # Check if the database file already exists 
            # and load it if available

            if os.path.exists(self.DB_PATH):
                print("Database file exists:", self.DB_PATH)

                # Load the existing vector store from the database file
                embeddings = GoogleGenerativeAIEmbeddings(
                    model="models/gemini-embedding-001",
                    google_api_key=self.api_key,
                    task_type="retrieval_document"
                )

                self.vector_store = Chroma(
                    persist_directory=self.DB_PATH,
                    embedding_function=embeddings,
                )

                print(
                "Collection count:",
                self.vector_store._collection)

                return (
                self.vector_store,
                0,
                self.vector_store._collection.count()
            )

            self.load_file()
            self.transcribe()
            self.create_documents()
            self.split_documents()
            self.create_vector_store()

            return self.vector_store, len(self.documents), len(self.chunks)
        
        except (DocumentLoadError, DocumentValidationError, DocumentSplitError, DocumentSaveError) as e:
            print(f"Error processing audio file: {e}")
            return None
        except Exception as e:
            
            print(f"Unexpected error processing audio file: {e}")
            traceback.print_exc()
            
            return None
        
        finally:
            if self.file_path and os.path.exists(self.file_path):
                os.remove(self.file_path)   

    def __str__(self):
        return f"AudioProcessor(file_path={self.file_path}, " \
               f"chunks={'available' if self.chunks else 'not available'}, " \
               f"transcript={'available' if self.transcript else 'not available'})"
