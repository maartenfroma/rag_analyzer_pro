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
    DocumentLoadError,
    DocumentSplitError,
    DocumentValidationError,
    DocumentSaveError,
)

from rag_components.helpers.metadata_helper import MetadataHelper

import subprocess

import logging

logger = logging.getLogger(__name__)

from dotenv import load_dotenv

load_dotenv()

#============================
# Environment Variables
#============================   
# Load the Chroma database path from environment variables
CHROMA_PATH = os.getenv("CHROMA_PATH")


# Load the embedding model from environment variables
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")


#============================================================
# Video Processor Class
#============================================================

class VideoProcessor(BaseMediaProcessor):
    


    def __init__(
        self,
        file_bytes: bytes,
        api_key: str,
        file_name: str,
        model_size="small",
        chunk_size=1000,
        chunk_overlap=200,
    ):

        self.temp_file = None
        self.model = WhisperModel(model_size)
        self.transcript = None
        self.chunks = None
        self.segments = None
        self.vector_store = None
        self.file_bytes = file_bytes
        self.video_path = None
        self.audio_path = None
        self.api_key = api_key
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.documents = []
        self.file_name = file_name
        self.DB_PATH = os.path.join(CHROMA_PATH, Path(self.file_name).stem)

    # Load the video file from the given path or from the temporary file if no path is provided
    # file_path: Path to the video file. If None, the temporary file will be used.

    def load_file(self, file_path=None):
        try:
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=Path(self.file_name).suffix
            ) as temp_file:
                temp_file.write(self.file_bytes)
                temp_file.flush()
                self.video_path = temp_file.name
            return self.video_path
        except Exception as e:
            raise DocumentLoadError("Failed to load video file.") from e

    # Extract audio from the loaded video file
    # Returns the path to the extracted audio file
    # Raises ValueError if the video file is not loaded
    def extract_audio(self, output_format="wav"):

        if not self.video_path:
            
            raise ValueError(
                "File not loaded. Call load_file() first."
            )

        audio_temp = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".wav"
        )
        audio_temp.close()

        result = subprocess.run(
            [
                "ffmpeg",
                "-i",
                self.video_path,
                "-vn",
                "-ar",
                "16000",
                "-ac",
                "1",
                "-y",
                audio_temp.name,
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise DocumentLoadError(result.stderr)

        self.audio_path = audio_temp.name

        return self.audio_path
    # Transcribe the loaded video file into text
    # Returns the transcript as a string
    # Raises ValueError if the file is not loaded or does not exist

    def transcribe(self):
        if not self.audio_path:
            raise ValueError("Audio not extracted. Call extract_audio() first.")

        segments, _ = self.model.transcribe(self.audio_path)

        self.segments = list(segments)

        self.transcript = " ".join(seg.text for seg in self.segments)

        # Return the generated transcript as a string
        return self.transcript
    
    # Create documents from the transcript
    # Returns a list of Document objects
    # Raises ValueError if the transcript is not available

    def create_documents(self):

        logger.info("Creating documents from transcript.")
        if not self.transcript:
            raise DocumentValidationError(
                "Transcript not available. " "Call transcribe() first."
            )
    

        logger.info("Creating document from full text.")
        document = Document(
            page_content=self.transcript,
            metadata=MetadataHelper.build_metadata(
                source="video", file_name=self.file_name
            ),
        )

        self.documents = [document]
        logger.info("Document created successfully.")
        return self.documents

    # Split the documents into chunks for further processing
    # Returns a list of text chunks
    # Raises ValueError if no documents are available

    def split_documents(self):
        if not self.documents:
            raise DocumentValidationError(
                "No documents available. Call create_documents() first."
            )

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", " ", ""],
        )

        self.chunks = text_splitter.split_documents(self.documents)

        logger.info("Number of chunks created: %d", len(self.chunks))

        for chunk in self.chunks[:5]:
            logger.info("Chunk preview: %s", chunk.page_content[:500])

        return self.chunks

    # Create a vector store from the chunks
    # Returns the vector store object
    # Raises ValueError if no chunks are available

    def create_vector_store(self):
        if not self.chunks:
            raise DocumentSplitError(
                "No chunks available. Call split_documents() first."
            )

        embeddings = GoogleGenerativeAIEmbeddings(
            model=EMBEDDING_MODEL,
            google_api_key=self.api_key,
            task_type="retrieval_document",
        )
        
        
        db_file = os.path.join(
        self.DB_PATH,
        "chroma.sqlite3"
        )

        if os.path.exists(db_file):
            logger.info("Loading existing database file: %s", db_file)
            self.vector_store = Chroma(
                persist_directory=self.DB_PATH,
                embedding_function=embeddings,
            )
        else:
            logger.info("Creating new database file: %s", db_file)
            self.vector_store = Chroma.from_documents(
                documents=self.chunks,
                embedding=embeddings,
                persist_directory=self.DB_PATH,
            )
        return self.vector_store

    # Process the video file: load, transcribe, create documents, split, and create vector store
    # Returns the vector store, number of documents, and number of chunks
    # Raises RuntimeError if any step fails

    def process(self):
        try:
            os.environ["GOOGLE_API_KEY"] = self.api_key
            
            
            db_file = os.path.join(self.DB_PATH, "chroma.sqlite3")

            if os.path.exists(db_file):
                logger.info("Chroma database file exists: %s", db_file)
                embeddings = GoogleGenerativeAIEmbeddings(
                    model=EMBEDDING_MODEL,
                    google_api_key=self.api_key,
                    task_type="retrieval_document",
                )
                self.vector_store = Chroma(
                    persist_directory=self.DB_PATH,
                    embedding_function=embeddings,
                )
                return self.vector_store, 0, self.vector_store._collection.count()

            
            self.load_file()
            logger.info("Video file loaded successfully.")

            self.extract_audio()
            logger.info("Extracting audio from video.")
            self.transcribe()
            logger.info("Transcription completed successfully. Transcript length: %d", len(self.transcript))
            self.create_documents()
            logger.info("Documents created successfully. Number of documents: %d", len(self.documents))
            self.split_documents()
            logger.info("Documents split into chunks successfully. Number of chunks: %d", len(self.chunks))
            self.create_vector_store()
            logger.info("Vector store created successfully.")

            return self.vector_store, len(self.chunks), len(self.documents)

        except (
            DocumentLoadError,
            DocumentValidationError,
            DocumentSplitError,
            DocumentSaveError,
        ) as e:
            logger.error("Error processing video file: %s", e)
            raise 
        
        except Exception:
            logger.error("Unexpected error processing video file: %s")
            raise

        finally:
            if self.video_path and os.path.exists(self.video_path):
                os.remove(self.video_path)
            if self.audio_path and os.path.exists(self.audio_path):
                os.remove(self.audio_path)

    def __str__(self):
        return (
            f"VideoProcessor(video_path={self.video_path}, "
            f"chunks={'available' if self.chunks else 'not available'}, "
            f"transcript={'available' if self.transcript else 'not available'}, "
            f"vector_store={'available' if self.vector_store else 'not available'})"
        )
