
import os
import tempfile
import pandas as pd
from rag_components.processors.base.base_document_processor import BaseDocProcessor
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.documents import Document
from langchain_chroma import Chroma 

class CsvProcessor(BaseDocProcessor):

    def __init__(self, file_bytes, api_key: str, chunk_size: int=1000, 
                 chunk_overlap: int=200):
        self.file_bytes=file_bytes
        self.api_key=api_key
        self.chunk_size=chunk_size
        self.chunk_overlap=chunk_overlap

        self.temp_path: str | None = None
        self.documents=None
        self.chunks=None
        self.vector_store=None

    def load_file(self):
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as temp_file:
                temp_file.write(self.file_bytes)
                self.temp_path = temp_file.name
        except Exception as e:
            raise RuntimeError(f"Error loading CSV file: {e}")

    def extract_pages(self):
        try:
            self.documents = []
            df = pd.read_csv(self.temp_path)
            self.documents.append(Document(page_content=df.to_csv(index=False), metadata={"source": "csv", "table": "sheet1"}))
        except Exception as e:
            raise RuntimeError(f"Error extracting pages from CSV file: {e}")      

        return self.documents

    def split_documents(self):
        try:
            if not self.documents:
                raise ValueError("No documents to split. Please extract pages first.")

            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap
            )
            self.chunks = []
            for doc in self.documents:
                text = doc.page_content
                for chunk in text_splitter.split_text(text):
                    self.chunks.append(Document(page_content=chunk, metadata={
                        "source": "csv",
                        "table": doc.metadata.get("table", "")
                    }))
        except Exception as e:
            raise RuntimeError(f"Error splitting CSV documents: {e}")

        return self.chunks

    def create_vector_store(self):
        try:
            if not self.chunks:
                raise ValueError("No chunks to create vector store. Please split documents first.")
        
            embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", 
                                                      google_api_key=self.api_key, 
                                                      task_type="retrieval_document")
            self.vector_store = Chroma.from_documents(self.chunks, embeddings)
        except Exception as e:
            raise RuntimeError(f"Error creating vector store from CSV chunks: {e}")

        return self.vector_store    

    def process(self):
        try:
            os.environ["GOOGLE_API_KEY"] = self.api_key

            self.load_file()
            self.extract_pages()
            self.split_documents()
            self.create_vector_store()

            #Return the vector store, number of chunks, and number of documents
            return self.vector_store, len(self.chunks), len(self.documents)
        
        except Exception as e:
            raise RuntimeError(f"Error processing CSV file: {e}")

        
        finally:
            if self.temp_path and os.path.exists(self.temp_path):
                os.remove(self.temp_path)   

    def __str__(self):
               return super().__str__() + f" (temp_path={self.temp_path}, " \
                      f"documents={len(self.documents) if self.documents else 0}, " \
                      f"chunks={len(self.chunks) if self.chunks else 0})"