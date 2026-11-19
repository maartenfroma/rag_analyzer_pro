import os
import tempfile
from pathlib import Path
import pandas as pd

from rag_components.processors.base.base_document_processor import BaseDocProcessor
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.documents import Document
from langchain_chroma import Chroma

from rag_components.exceptions.document_exceptions import (
    DocumentLoadError,
    DocumentSplitError,
    DocumentValidationError,
    DocumentSaveError,
)

from rag_components.helpers.metadata_helper import MetadataHelper

import logging

from dotenv import load_dotenv


logger = logging.getLogger(__name__)

load_dotenv()

# Load the Chroma database path from environment variables
CHROMA_PATH = os.getenv("CHROMA_PATH")  

# Load the embedding model from environment variables
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
    
class CsvProcessor(BaseDocProcessor):
    

    
    MAX_ROWS = 2000
    MAX_CHUNKS = 500

    def __init__(
        self,
        file_bytes,
        api_key: str,
        file_name: str,
        chunk_size: int = 5000,
        chunk_overlap: int = 50,
    ):
        self.file_bytes = file_bytes
        self.api_key = api_key
        self.file_name = file_name
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        self.temp_path: str | None = None
        self.documents = None
        self.chunks = None
        self.vector_store = None

        self.DB_PATH = os.path.join(CHROMA_PATH, Path(self.file_name).stem)

    def load_file(self):
        try:
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=Path(self.file_name).suffix
            ) as temp_file:
                temp_file.write(self.file_bytes)
                self.temp_path = temp_file.name
        except Exception as e:
            raise DocumentLoadError(f"Error loading CSV file: {self.file_name}") from e
        return self.temp_path

    def extract_pages(self):
        try:
            self.documents = []
            df = pd.read_csv(self.temp_path)
            if len(df) > self.MAX_ROWS:
                df = df.head(self.MAX_ROWS)
            if len(df) == 0:
                raise DocumentValidationError(
                    f"CSV file is empty after applying MAX_ROWS limit: {self.file_name}"
                )
            self.documents.append(
                Document(
                    page_content=df.to_csv(index=False),
                    metadata={"source": "csv", "table": "sheet1"},
                )
            )
        except Exception as e:
            raise DocumentLoadError(
                f"Error extracting pages from CSV file: {self.file_name}"
            ) from e

        return self.documents

    def split_documents(self):
        try:
            if not self.documents:
                raise DocumentValidationError(
                    "No documents to split. Please extract pages first."
                )

            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap,
                separators=["\n\n", "\n", " ", ""]
            )
            self.chunks = []
            
            for i, doc in enumerate(self.documents):
                
                
                text = doc.page_content
                for chunk in text_splitter.split_text(text):
                    metadata = MetadataHelper.build_metadata(
                        source="csv",
                        file_name=self.file_name,
                        index=i,
                        chunk_index=len(self.chunks),
                    )
                    logger.info(metadata)
                    # Append the chunk with its metadata to the list
                    # of chunks
                    
                    if len(self.chunks) < self.MAX_CHUNKS:
                        self.chunks.append(Document(page_content=chunk, metadata=metadata))
                        
                    else:
                        logger.info("Reached MAX_CHUNKS limit for chunks. Stopping further chunking.")
                        break

        
        except Exception as e:
            raise DocumentSplitError(
                f"Error splitting CSV documents: {self.file_name}"
            ) from e

        return self.chunks

    def create_vector_store(self):

        try:

            # Check if there are any chunks to create the vector store from
            if not self.chunks:
                raise DocumentValidationError(
                    "No chunks to create vector store. Please split documents first."
                )

            embeddings = GoogleGenerativeAIEmbeddings(
                model=EMBEDDING_MODEL,
                google_api_key=self.api_key,
                task_type="retrieval_document",
            )
            # Define the path to the Chroma database file
            db_file = os.path.join(self.DB_PATH, "chroma.sqlite3")

            # Check if the Chroma database file exists
            if os.path.exists(db_file):
                logger.info("Vector store already exists. Loading existing store.")
                self.vector_store = Chroma(
                    persist_directory=self.DB_PATH, embedding_function=embeddings
                )
                return self.vector_store

            # If the Chroma database file does not exist, create a new vector store
            else:
                logger.info(f"Creating new vector store {self.DB_PATH}.")
                os.makedirs(self.DB_PATH, exist_ok=True)
                
                # Create the vector store from the document chunks and persist it to 
                # the Chroma database
                
                try:
                    self.vector_store = Chroma.from_documents(
                        documents=self.chunks,
                        embedding=embeddings,
                        persist_directory=self.DB_PATH,
                    )
                        
                except Exception as e:
                    raise DocumentSaveError(
                        f"Error creating vector store from CSV chunks: {self.file_name}"
                    ) from e
                    
        except Exception as e:
            raise DocumentSaveError(
                f"Error creating vector store from CSV chunks: {self.file_name}"
            ) from e
        return self.vector_store
   
   
    def process(self):

        try:
            os.environ["GOOGLE_API_KEY"] = self.api_key

            if os.path.exists(self.DB_PATH):

                # If the Chroma database path exists, we can load
                # the existing embeddings

                embeddings = GoogleGenerativeAIEmbeddings(
                    model=EMBEDDING_MODEL, 
                    google_api_key=self.api_key,
                    task_type="retrieval_document",
                )

                logger.info(
                    "Loaded existing embeddings for Chroma database path: %s",
                    self.DB_PATH,
                )

                self.vector_store = Chroma(
                    persist_directory=self.DB_PATH,
                    embedding_function=embeddings,
                )
                logger.info("Chroma database path exists: %s", self.DB_PATH)

                return (self.vector_store, 0, self.vector_store._collection.count())
            else:
                logger.info("Chroma database path does not exist: %s", self.DB_PATH)
                logger.info("Starting processing for CSV file: %s", self.file_name)
                logger.info("Processing CSV document: %s", self.file_name)
                logger.info("Loading CSV file: %s", self.file_name)
                self.load_file()

                logger.info("Extracting pages from CSV file: %s", self.file_name)
                self.extract_pages()
                logger.info("Splitting CSV document into chunks: %s", self.file_name)
                self.split_documents()
                logger.info("Creating vector store from CSV chunks: %s", self.file_name)
                self.create_vector_store()

                logger.info(
                    "Returning vector store, number of chunks, and number of documents for CSV file: %s",
                    self.file_name,
                )

                # Return the vector store, number of chunks, and number of documents
            return self.vector_store, len(self.chunks), len(self.documents)

        finally:
            if self.temp_path and os.path.exists(self.temp_path):
                os.remove(self.temp_path)

    def __str__(self):
        return (
            super().__str__() + f" (temp_path={self.temp_path}, "
            f"documents={len(self.documents) if self.documents else 0}, "
            f"chunks={len(self.chunks) if self.chunks else 0})"
        )
