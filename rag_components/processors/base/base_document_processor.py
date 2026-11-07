from abc import ABC, abstractmethod


class BaseDocProcessor(ABC):

    # ABSTRACT METHODS FOR DOCUMENT PROCESSING
    
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