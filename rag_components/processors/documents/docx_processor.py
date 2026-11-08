
import os
from rag_components.processors.base.base_document_processor import BaseDocProcessor
from langchain_community.document_loaders import Docx2txtLoader
import tempfile
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document


class DocxProcessor(BaseDocProcessor):

    #INITIALISEER PROJECT VARIABLES
    def __init__(self, api_key: str, file_bytes: bytes, chunk_size: int=1000, 
                 chunk_overlap: int=200):
        
        
        self.api_key = api_key
        self.file_bytes = file_bytes
        self.temp_path:str | None = None
        self.documents = None
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.chunks = None
        self.vector_store = None

    #LOAD FILE
    def load_file(self):
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as temp_file:
            temp_file.write(self.file_bytes)
            self.temp_path = temp_file.name
        return self.temp_path

    

    #EXTRACT PAGES FROM DOCX
    def extract_pages(self):
        loader = Docx2txtLoader(self.temp_path)
        self.documents = loader.load()
        return self.documents


    #Split documents into chunks
    def split_documents(self):
        if not self.documents:
            raise ValueError("No documents to split. Please extract pages first.")

        
        # Initialize the text splitter with the specified chunk size, overlap, and separators
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )
        self.chunks = []
        for doc in self.documents:
            text = doc.page_content
            for chunk in text_splitter.split_text(text):
                self.chunks.append(Document(page_content=chunk, metadata={
                    "source": "docx"
                }))

        #Return the chunks as a list of documents
        return self.chunks

    def create_vector_store(self):
        if not self.chunks:
            raise ValueError("No chunks to create vector store from. Please split documents first.")


        embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", 
                                                  google_api_key=self.api_key, 
                                                  task_type="retrieval_document")

        self.vector_store = Chroma.from_documents(self.chunks, embeddings)

        #Return the created vector store
        return self.vector_store

    #PROCESS THE DOCX FILE
    def process(self):
        try:
            os.environ["GOOGLE_API_KEY"] = self.api_key
            self.load_file()
            self.extract_pages()
            self.split_documents()
            self.create_vector_store()

            return (self.vector_store, len(self.documents), len(self.chunks))

        except Exception as e:
            raise RuntimeError(f"Error processing DOCX: {e}")

        finally:
            if self.temp_path and os.path.exists(self.temp_path):
                os.remove(self.temp_path)

    def __str__(self):
                return super().__str__() + f" (temp_path={self.temp_path}, " \
                       f"documents={len(self.documents) if self.documents else 0}, " \
                       f"chunks={len(self.chunks) if self.chunks else 0})"