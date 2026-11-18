import os
from pathlib import Path
from rag_components.processors.base.base_document_processor import BaseDocProcessor
from langchain_community.document_loaders import Docx2txtLoader
import tempfile
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

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

class DocxProcessor(BaseDocProcessor):

    # INITIALISEER PROJECT VARIABLES
    def __init__(
        self,
        api_key: str,
        file_bytes: bytes,
        file_name: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ):

        self.api_key = api_key
        self.file_bytes = file_bytes
        self.temp_path: str | None = None
        self.documents = None
        self.chunk_size = chunk_size
        self.file_name = file_name
        self.chunk_overlap = chunk_overlap
        self.chunks = None
        self.vector_store = None
        self.DB_PATH = os.path.join("chroma_db", Path(self.file_name).stem)

    # LOAD FILE
    def load_file(self):

        try:
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=Path(self.file_name).suffix
            ) as temp_file:
                temp_file.write(self.file_bytes)
                self.temp_path = temp_file.name
            return self.temp_path
        except Exception as e:
            raise DocumentLoadError(f"Error loading DOCX file: {self.file_name}") from e

    # EXTRACT PAGES FROM DOCX
    def extract_pages(self):

        try:
            loader = Docx2txtLoader(self.temp_path)
            self.documents = loader.load()
            return self.documents
        except Exception as e:
            raise DocumentLoadError(
                f"Error extracting pages from DOCX file: {self.file_name}"
            ) from e

    # Split documents into chunks
    def split_documents(self):

        try:
            if not self.documents:
                raise DocumentValidationError(
                    "No documents to split. Please extract pages first."
                )

            # Initialize the text splitter with the specified chunk size, overlap, and separators
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
                        source="docx",
                        file_name=self.file_name,
                        index=i,
                        chunk_index=len(self.chunks),
                    )
                    logger.info(metadata)
                    self.chunks.append(Document(page_content=chunk, metadata=metadata))
        except Exception as e:
            raise DocumentSplitError(
                f"Error splitting DOCX documents: {self.file_name}"
            ) from e

        # Return the chunks as a list of documents
        return self.chunks

    def create_vector_store(self):

        try:

            # Check if there are any chunks to create the vector store from
            if not self.chunks:
                raise DocumentValidationError(
                    "No chunks to create vector store. Please split documents first."
                )

            embeddings = GoogleGenerativeAIEmbeddings(
                model=os.getenv("EMBEDDING_MODEL"),
                google_api_key=self.api_key,
                task_type="retrieval_document",
            )
            if os.path.exists(self.DB_PATH):
                logger.info("Loading existing database file: %s", self.DB_PATH)
                self.vector_store = Chroma(
                    persist_directory=self.DB_PATH,
                    embedding_function=embeddings,
                )
            else:
                logger.info("Creating new database file: %s", self.DB_PATH)
                
                try:
                    self.vector_store = Chroma.from_documents(
                        documents=self.chunks,
                        embedding=embeddings,
                        persist_directory=self.DB_PATH,
                    )
                except Exception as e:
                    raise DocumentSaveError(
                        f"Error creating vector store from DOCX chunks: {self.file_name}"
                    ) from e
               
                # self.vector_store = Chroma.from_documents(
                #     documents=self.chunks,
                #     embedding=embeddings,
                #     persist_directory=self.DB_PATH,
                # )
        except Exception as e:
            raise DocumentSaveError(
                f"Error creating vector store from DOCX chunks: {self.file_name}"
            ) from e

        return self.vector_store

    # PROCESS THE DOCX FILE
    def process(self):
        try:
            os.environ["GOOGLE_API_KEY"] = self.api_key

            if os.path.exists(self.DB_PATH):
                logger.info("Chroma database path exists: %s", self.DB_PATH)

                embeddings = GoogleGenerativeAIEmbeddings(
                    model=os.getenv("EMBEDDING_MODEL"),
                    google_api_key=self.api_key,
                    task_type="retrieval_document",
                )
                self.vector_store = Chroma(
                    persist_directory=self.DB_PATH,
                    embedding_function=embeddings,
                )

                return (self.vector_store, 0, self.vector_store._collection.count())

            else:
                logger.info("Chroma database path does not exist: %s", self.DB_PATH)
                logger.info("Loading DOCX file: %s", self.file_name)
                self.load_file()
                logger.info("Extracting pages from DOCX file: %s", self.file_name)
                self.extract_pages()
                logger.info("Splitting DOCX file into chunks: %s", self.file_name)
                self.split_documents()
                logger.info(
                    "Creating vector store from DOCX chunks: %s", self.file_name
                )
                self.create_vector_store()

            return (self.vector_store, len(self.documents), len(self.chunks))

        finally:
            if self.temp_path and os.path.exists(self.temp_path):
                os.remove(self.temp_path)

    def __str__(self):
        return (
            super().__str__() + f" (temp_path={self.temp_path}, "
            f"documents={len(self.documents) if self.documents else 0}, "
            f"chunks={len(self.chunks) if self.chunks else 0})"
        )
