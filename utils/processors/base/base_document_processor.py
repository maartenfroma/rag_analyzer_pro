from abc import ABC, abstractmethod


class BaseDocProcessor(ABC):

    #Replace and strip
    def clean_text(self, text: str):

        text = text.replace("\n", " ").replace("\n\n", "\n")

        return text.strip()

    @abstractmethod
    def process(self):
        pass