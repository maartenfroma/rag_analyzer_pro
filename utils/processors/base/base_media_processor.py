from base.base_document_processor import BaseDocProcessor
from abc import abstractmethod
from abc import ABC, abstractmethod

class BaseMediaProcessor(ABC): 


    @abstractmethod
    def load_file(self):
            pass
    
    
    @abstractmethod
    def transcribe(self):
            pass

    @abstractmethod
    def create_documents(self):
            pass        
    
    @abstractmethod
    def process(self):
            pass
   