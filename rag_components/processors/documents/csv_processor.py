
import os
import tempfile
from pathlib import Path
import pandas as pd
from rag_components.processors.base.base_document_processor import BaseDocProcessor
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.documents import Document
from langchain_chroma import Chroma 

import textstat

from rag_components.exceptions.document_exceptions import (
    DocumentLoadError, DocumentSplitError, 
    DocumentValidationError, DocumentSaveError)

from rag_components.helpers.metadata_helper import MetadataHelper

class CsvProcessor(BaseDocProcessor):

    
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
            raise DocumentLoadError(f"Error loading CSV file: {self.file_name}") from e
        return self.temp_path

    def extract_pages(self):
        try:
            self.documents = []
            df = pd.read_csv(self.temp_path)
            self.documents.append(Document(page_content=df.to_csv(index=False), metadata={"source": "csv", "table": "sheet1"}))
        except Exception as e:
            raise DocumentLoadError(f"Error extracting pages from CSV file: {self.file_name}") from e

        return self.documents

    def split_documents(self):
        try:
            if not self.documents:
                raise DocumentValidationError("No documents to split. Please extract pages first.")

            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap
            )
            self.chunks = []
            for i, doc in enumerate(self.documents):
                text = doc.page_content
                for chunk in text_splitter.split_text(text):
                    metadata=MetadataHelper.build_metadata(
                      source="csv",
                       file_name=self.file_name,
                       index=i,
                       chunk_index=len(self.chunks)
                    )
                    print(doc.metadata)
                    # Append the chunk with its metadata to the list 
                    # of chunks
                    self.chunks.append(Document(page_content=chunk, metadata=metadata))
                        
        except Exception as e:
            raise DocumentSplitError(f"Error splitting CSV documents: {self.file_name}") from e

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
            # Define the path to the Chroma database file
            db_file=os.path.join(self.DB_PATH, "chroma.sqlite3")

            # Check if the Chroma database file exists
            if os.path.exists(db_file):
                print("Vector store already exists. Loading existing store.")
                self.vector_store = Chroma(persist_directory=self.DB_PATH,
                                            embedding_function=embeddings)
                return self.vector_store
            
            # If the Chroma database file does not exist, create a new vector store
            else:
                print(
                    f"Creating new vector store {self.DB_PATH}.")
                os.makedirs(self.DB_PATH, exist_ok=True)
                self.vector_store = Chroma.from_documents(documents=self.chunks, embedding=embeddings,
                                                            persist_directory=self.DB_PATH)
                return self.vector_store
            
        except Exception as e:
                raise DocumentSaveError(f"Error creating vector store from CSV chunks: {self.file_name}") from e
            

           
    def process(self):
        try:
            os.environ["GOOGLE_API_KEY"] = self.api_key

            self.load_file()
            self.extract_pages()
            self.split_documents()
            self.create_vector_store()

            #Return the vector store, number of chunks, and number of documents
            return self.vector_store, len(self.chunks), len(self.documents)
        


        
        finally:
            if self.temp_path and os.path.exists(self.temp_path):
                os.remove(self.temp_path)   

    def __str__(self):
               return super().__str__() + f" (temp_path={self.temp_path}, " \
                      f"documents={len(self.documents) if self.documents else 0}, " \
                      f"chunks={len(self.chunks) if self.chunks else 0})"