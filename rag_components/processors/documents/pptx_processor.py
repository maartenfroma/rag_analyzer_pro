import os
import tempfile
from pathlib import Path
from rag_components.processors.base.base_document_processor import BaseDocProcessor
import traceback
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from pptx import Presentation


from rag_components.exceptions.document_exceptions import (
    DocumentLoadError,
    DocumentSplitError,
    DocumentValidationError,
    DocumentSaveError,
)

from rag_components.helpers.metadata_helper import MetadataHelper

import logging

logger = logging.getLogger(__name__)

from dotenv import load_dotenv
load_dotenv()


class PPTXProcessor(BaseDocProcessor):

    def __init__(
        self,
        file_bytes,
        api_key: str,
        file_name: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ):
        self.file_bytes = file_bytes
        self.api_key = api_key
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        self.temp_path: str | None = None

        self.documents = None
        self.chunks = None
        self.vector_store = None

        self.file_name = file_name

        self.DB_PATH = os.path.join("chroma_db", Path(self.file_name).stem)

    def load_file(self):
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pptx") as temp_file:
                temp_file.write(self.file_bytes)
                self.temp_path = temp_file.name
        except Exception as e:
            raise DocumentLoadError(f"Error loading PPTX file: {self.file_name}") from e

    def extract_pages(self):
        try:
            presentation = Presentation(self.temp_path)
            self.documents = []

            for idx, slide in enumerate(presentation.slides, start=1):

                slide_parts = []
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        text = shape.text.strip()

                        if text:
                            slide_parts.append(text)
                            slide_text = "\n".join(slide_parts)

                            if slide_text:
                                metadata = MetadataHelper.build_metadata(
                                    source="pptx", file_name=self.file_name, slide=idx
                                )

                                self.documents.append(
                                    Document(page_content=slide_text, metadata=metadata)
                                )

                if not self.documents:
                    logger.error(
                        "No pages extracted from PPTX file: %s", self.file_name
                    )
                    raise DocumentLoadError(
                        f"No pages extracted from PPTX file: {self.file_name}"
                    )
        except Exception as e:
            logger.error("Error extracting pages from PPTX file: %s", self.file_name)
            raise DocumentLoadError(
                f"Error extracting pages from PPTX file: {self.file_name}"
            ) from e

        return self.documents

    def split_documents(self):
        try:
            if not self.documents:
                raise DocumentValidationError(
                    "No documents to split. Please extract pages first."
                )

            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap
            )
            self.chunks = []
            for idx, doc in enumerate(self.documents):
                text = doc.page_content
                for chunk in text_splitter.split_text(text):
                    metadata = MetadataHelper.build_metadata(
                        source="pptx",
                        file_name=self.file_name,
                        index=idx,
                        chunk_index=len(self.chunks),
                    )
                    self.chunks.append(Document(page_content=chunk, metadata=metadata))

        except Exception as e:
            raise DocumentSplitError(
                f"Error splitting PPTX documents: {self.file_name}"
            ) from e

        return self.chunks

    def create_vector_store(self):
        try:
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
                self.vector_store = Chroma.from_documents(
                    documents=self.chunks,
                    embedding=embeddings,
                    persist_directory=self.DB_PATH,
                )
        except Exception as e:
            raise DocumentSaveError(
                f"Error creating vector store from PPTX chunks: {self.file_name}"
            ) from e

        return self.vector_store

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

            logger.info("Loading PPTX file: %s", self.file_name)
            self.load_file()
            logger.info("Extracting pages from PPTX file: %s", self.file_name)
            self.extract_pages()
            logger.info("Splitting PPTX document into chunks: %s", self.file_name)
            self.split_documents()
            logger.info("Creating vector store from PPTX chunks: %s", self.file_name)
            self.create_vector_store()

            logger.info(
                "Returning vector store, number of chunks, and number of documents for PPTX file: %s",
                self.file_name,
            )
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
