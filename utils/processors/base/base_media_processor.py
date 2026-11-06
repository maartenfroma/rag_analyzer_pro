from base.base_document_processor import BaseDocProcessor
from abc import abstractmethod

class BaseMediaProcessor(BaseDocProcessor): 


    @abstractmethod
    def load_file(self):
            pass
    
    
    @abstractmethod
    def extract_pages(self):
            pass
    
    @abstractmethod
    def split_documents(self):
            pass
    
    @abstractmethod
    def create_vector_store(self):
            pass
       
    @abstractmethod
    def process(self):
            pass
   