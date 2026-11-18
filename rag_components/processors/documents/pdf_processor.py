import os
import tempfile
from pathlib import Path

from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from rag_components.processors.base.base_document_processor import BaseDocProcessor
from langchain_core.documents import Document


from rag_components.exceptions.document_exceptions import (
    DocumentLoadError,
    DocumentSplitError,
    DocumentValidationError,
    DocumentSaveError,
)

from rag_components.helpers.metadata_helper import MetadataHelper

import logging

logger = logging.getLogger(__name__)


class PdfProcessor(BaseDocProcessor):

    # INITIALISEER PROJECT
    def __init__(
        self,
        file_bytes,
        api_key: str,
        file_name: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ):
        self.file_name = file_name
        self.file_bytes = file_bytes
        self.api_key = api_key
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Temporary path for the uploaded PDF file
        self.temp_path: str | None = None
        self.documents = None
        self.chunks = None
        self.vector_store = None

        self.DB_PATH = os.path.join("chroma_db", Path(self.file_name).stem)

    # LOAD FILE
    def load_file(self):

        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                temp_file.write(self.file_bytes)
                self.temp_path = temp_file.name

            return self.temp_path
        except Exception as e:
            raise DocumentLoadError(f"Error loading PDF file: {self.file_name}") from e

    # EXTRACT PAGES FROM PDF
    def extract_pages(self):
        loader = PyMuPDFLoader(self.temp_path)
        self.documents = loader.load()

        # Return the extracted pages as a list of documents
        return self.documents

    # SPLIT DOCUMENTS INTO CHUNKS
    def split_documents(self):

        if not self.documents:
            raise DocumentValidationError(
                "No documents to split. Please extract pages first."
            )

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", " ", ""],
        )

        self.chunks = []

        for i, doc in enumerate(self.documents):
            text = doc.page_content
            for chunk in text_splitter.split_text(text):
                metadata = MetadataHelper.build_metadata(
                    source="pdf",
                    file_name=self.file_name,
                    index=i,
                    chunk_index=len(self.chunks),
                    page_number=(
                        doc.metadata.get("page_number") if doc.metadata else None
                    ),
                )
                self.chunks.append(Document(page_content=chunk, metadata=metadata))
        return self.chunks

    # CREATE VECTOR STORE FROM CHUNKS
    def create_vector_store(self):

        try:

            # Check if there are any chunks to create the vector store from
            if not self.chunks:
                raise DocumentValidationError(
                    "No chunks to create vector store. Please split documents first."
                )

            embeddings = GoogleGenerativeAIEmbeddings(
                model="models/gemini-embedding-001",
                google_api_key=self.api_key,
                task_type="retrieval_document",
            )

            # Check if the Chroma database file exists
            if os.path.exists(self.DB_PATH):
                logger.info("Vector store already exists. Loading existing store.")
                self.vector_store = Chroma(
                    persist_directory=self.DB_PATH, embedding_function=embeddings
                )
                return self.vector_store

            # If the Chroma database file does not exist, create a new vector store
            else:
                logger.info("Creating new vector store: %s", self.DB_PATH)
                os.makedirs(self.DB_PATH, exist_ok=True)
                
                try:
                    self.vector_store = Chroma.from_documents(
                        documents=self.chunks,
                        embedding=embeddings,
                        persist_directory=self.DB_PATH,
                    )
                except Exception as e:
                    raise DocumentSaveError(
                        f"Error creating vector store from PDF chunks: {self.file_name}"
                    ) from e
                return self.vector_store

        except Exception as e:
            raise DocumentSaveError(
                f"Error creating vector store from PDF chunks: {self.file_name}"
            ) from e

    # PROCESS THE PDF FILE
    def process(self):

        # Set the Google API key as an environment variable for the current process

        try:

            os.environ["GOOGLE_API_KEY"] = self.api_key

            if os.path.exists(self.DB_PATH):
                logger.info("Chroma database path exists: %s", self.DB_PATH)
                embeddings = GoogleGenerativeAIEmbeddings(
                    model="models/gemini-embedding-001",
                    google_api_key=self.api_key,
                    task_type="retrieval_document",
                )
                self.vector_store = Chroma(
                    persist_directory=self.DB_PATH,
                    embedding_function=embeddings,
                )
                return (self.vector_store, 0, self.vector_store._collection.count())

            logger.info("Processing PDF document: %s", self.file_name)

            logger.info("Loading PDF file: %s", self.file_name)
            self.load_file()
            logger.info("Extracting pages from PDF file: %s", self.file_name)
            self.extract_pages()
            logger.info("Splitting PDF document into chunks: %s", self.file_name)
            self.split_documents()
            logger.info("Creating vector store from PDF chunks: %s", self.file_name)
            self.create_vector_store()

            logger.info(
                "Returning vector store, number of chunks, and number of documents for PDF file: %s",
                self.file_name,
            )
            return (self.vector_store, len(self.chunks), len(self.documents))

        finally:
            if self.temp_path and os.path.exists(self.temp_path):
                os.remove(self.temp_path)

    def __str__(self):
        return (
            super().__str__() + f" (temp_path={self.temp_path}, "
            f"documents={len(self.documents) if self.documents else 0}, "
            f"chunks={len(self.chunks) if self.chunks else 0})"
        )
