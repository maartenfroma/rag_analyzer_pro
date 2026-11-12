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

    def split_documents(self):
        pass

    def create_vector_store(self):
        pass

    @abstractmethod
    def process(self):
        pass
