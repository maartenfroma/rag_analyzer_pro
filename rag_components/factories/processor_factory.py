from rag_components.processors.documents.pdf_processor import PdfProcessor
from rag_components.processors.documents.docx_processor import DocxProcessor
from rag_components.processors.documents.csv_processor import CsvProcessor
from rag_components.processors.documents.excel_processor import ExcelProcessor
from rag_components.processors.media.audio_processor import AudioProcessor
from rag_components.processors.documents.pptx_processor import PPTXProcessor
from rag_components.processors.media.video_processor import VideoProcessor

from rag_components.exceptions.document_exceptions import (
    UnsupportedDocumentException,
    DocumentLoadError,
    ProcessorCreationError,
    DocumentFileError,
)

from rag_components.exceptions.gemini_exceptions import GeminiAuthenticationError

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProcessorFactory:

    # Factory class to create appropriate processors based on file extension

    @staticmethod
    def create_processor(file_bytes: bytes, file_name: str, api_key: str):

        # Determine the file extension and create the appropriate
        # processor based on it
        logger.info(f"Creating processor for file: {file_name}")

        # Validate the input file bytes and file name before proceeding
        if not file_bytes:
            raise DocumentLoadError("File bytes are empty.")
        if not file_name:
            raise DocumentFileError("File name is empty.")

        # Extract the file extension from the file name and validate it
        if not "." in file_name:
            raise UnsupportedDocumentException(
                "File name does not contain an extension."
            )
        extension = "." + file_name.split(".")[-1].lower()

        # Validate the API key before creating the processor instance
        if not api_key:
            raise GeminiAuthenticationError("API key is missing.")
        logger.info("API key validated.")

        # Create the processor instance based on the file extension
        logger.info("Creating processor instance.")
        logger.info(f"File extension determined: {extension}")
        processors = {
            "pdf": PdfProcessor,
            "docx": DocxProcessor,
            "csv": CsvProcessor,
            "xlsx": ExcelProcessor,
            "mp3": AudioProcessor,
            "wav": AudioProcessor,
            "pptx": PPTXProcessor,
            "mp4": VideoProcessor,
        }

        logger.info(f"Available processors: {list(processors.keys())}")

        # Retrieve the processor class based on the file extension
        try:
            processor_class = processors.get(extension[1:])
        except Exception as e:
            logger.error(f"Error retrieving processor class: {e}")
            raise ProcessorCreationError(f"Error retrieving processor class: {e}")
        processor_class = processors.get(extension[1:])

        # Retrieve the processor class and handle unsupported extensions
        if not processor_class:
            logger.error(f"Unsupported file extension: {extension}")
            raise UnsupportedDocumentException(
                f"Unsupported file extension: {extension}"
            )
        logger.info(f"Processor class found: {processor_class.__name__}")

        # Return the instantiated processor object
        return processor_class(
            file_bytes=file_bytes, file_name=file_name, api_key=api_key
        )
