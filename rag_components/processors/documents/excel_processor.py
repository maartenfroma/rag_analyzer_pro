
import os
import tempfile
import pandas as pd
from rag_components.processors.base.base_document_processor import BaseDocProcessor
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma     
from langchain_core.documents import Document
from pathlib import Path


from rag_components.exceptions.document_exceptions import (
    DocumentLoadError, DocumentSplitError, 
    DocumentValidationError, DocumentSaveError)

from rag_components.helpers.metadata_helper import MetadataHelper

class ExcelProcessor(BaseDocProcessor):

    def __init__(self, file_bytes, api_key: str, file_name: str, chunk_size: int=1000, 
                 chunk_overlap: int=200):
        self.file_bytes=file_bytes
        self.api_key=api_key
        self.file_name=file_name
        self.chunk_size=chunk_size
        self.chunk_overlap=chunk_overlap

        self.temp_path: str | None = None
        self.documents=None
        self.chunks=None
        self.vector_store=None
        self.DB_PATH = os.path.join(
            "chroma_db",
            Path(self.file_name).stem
        )

    def load_file(self):
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(self.file_name).suffix) as temp_file:
                temp_file.write(self.file_bytes)
                self.temp_path = temp_file.name
        except Exception as e:
            raise DocumentLoadError(f"Error loading Excel file: {self.file_name}") from e

    def extract_pages(self):
        try:
            loader = pd.read_excel(self.temp_path, sheet_name=None)
            self.documents = []
            
            for sheet_name, df in loader.items():
                self.documents.append((sheet_name, df))
        
        except Exception as e:
            raise DocumentLoadError(f"Error extracting pages from Excel file: {self.file_name}") from e

        return self.documents   

    def split_documents(self):
        try:
            if not self.documents:
                raise DocumentValidationError("No documents to split. Please extract pages first.")

            # Initialize the text splitter for chunking the document text

            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap
            )
            #Return the list of chunks after splitting each document into smaller pieces
            self.chunks = []

            # Iterate over each document (sheet) and split its content 
            # into chunks
            for idx, (sheet_name, df) in enumerate(self.documents):

                text = df.to_csv(index=False)

                # Split the text of the current sheet into smaller chunks   
                for chunk in text_splitter.split_text(text):

                    # Build metadata for the current chunk using the MetadataHelper
                    metadata=MetadataHelper.build_metadata(
                        source="excel",
                        file_name=self.file_name,
                        table=sheet_name,
                        index=idx
                    )

                    # Append the current chunk along with its metadata to the list of chunks
                    self.chunks.append(Document(page_content=chunk, 
                                                metadata=metadata))  

        except Exception as e:
            raise DocumentSplitError(f"Error splitting Excel documents: {self.file_name}") from e

        #Return the list of chunks
        return self.chunks

    def create_vector_store(self):

        try:

            # Check if there are any chunks to create the vector store from
            if not self.chunks:
                raise DocumentValidationError("No chunks to create vector store. Please split documents first.")

            embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", 
                                                          google_api_key=self.api_key, 
                                                          task_type="retrieval_document",
                                                          )
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
        except Exception as e:
            raise DocumentSaveError(f"Error creating vector store from Excel chunks: {self.file_name}") from e

        return self.vector_store

    def process(self):
        try:
            os.environ["GOOGLE_API_KEY"] = self.api_key

            self.load_file()
            self.extract_pages()
            self.split_documents()
            self.create_vector_store()

            return self.vector_store, len(self.chunks), len(self.documents)

        finally:
            if self.temp_path and os.path.exists(self.temp_path):
                os.remove(self.temp_path)

    def __str__(self):
        return super().__str__() + f" (temp_path={self.temp_path}, " \
               f"documents={len(self.documents) if self.documents else 0}, " \
               f"chunks={len(self.chunks) if self.chunks else 0})"  