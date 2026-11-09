from rag_components.processors.documents.pdf_processor import PdfProcessor
from rag_components.processors.documents.docx_processor import DocxProcessor
from rag_components.processors.documents.csv_processor import CsvProcessor
from rag_components.processors.documents.excel_processor import ExcelProcessor
from rag_components.processors.media.audio_processor import AudioProcessor
from rag_components.processors.documents.pptx_processor import PPTXProcessor
from rag_components.processors.media.video_processor import VideoProcessor

class ProcessorFactory:

    # Factory class to create appropriate processors based on file extension

    @staticmethod
    def create_processor(file_bytes: bytes, file_name: str, api_key: str):

        # Determine the file extension and create the appropriate 
        # processor based on it

        extension = "." + file_name.split(".")[-1].lower()

        processors={
            "pdf": PdfProcessor,
            "docx": DocxProcessor,
            "csv": CsvProcessor,
            "xlsx": ExcelProcessor,
            "mp3": AudioProcessor,
            "wav": AudioProcessor,
            "pptx": PPTXProcessor,
            "mp4": VideoProcessor
        }

        processor_class = processors.get(extension[1:])
        if not processor_class:
            raise ValueError(f"Unsupported file extension: {extension}")
        return processor_class(file_bytes=file_bytes, 
                               file_name=file_name, api_key=api_key)