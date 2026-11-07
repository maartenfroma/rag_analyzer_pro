import os
import tempfile

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

from faster_whisper import WhisperModel
from moviepy import VideoFileClip

from base.base_media_processor import BaseMediaProcessor

class VideoProcessor(BaseMediaProcessor):

    def __init__(self, file_bytes: bytes, api_key:str, model_size="small", 
                 chunk_size=1000, chunk_overlap=200):
        
        self.temp_file = None
        self.model = WhisperModel(model_size)
        self.transcript = None
        self.chunks = None
        self.vector_store = None    
        self.file_bytes = file_bytes
        self.video_path = None
        self.audio_path = None
        self.api_key = api_key
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.documents = []     

    # Load the video file from the given path or from the temporary file if no path is provided
    # file_path: Path to the video file. If None, the temporary file will be used.

    def load_file(self, file_path=None):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
            temp_file.write(self.file_bytes)
            temp_file.flush()
            self.video_path = temp_file.name
        return self.video_path

    
    # Extract audio from the loaded video file
    # Returns the path to the extracted audio file
    # Raises ValueError if the video file is not loaded
    def extract_audio(self, output_format="wav"):

        if not self.video_path:
            raise ValueError("File not loaded. Call load_file() first.")
        audio_temp = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".wav"
        )

        audio_temp.close()

        video = VideoFileClip(self.video_path)

        video.audio.write_audiofile(
            audio_temp.name,
            logger=None
        )

        video.close()

        self.audio_path = audio_temp.name

        return self.audio_path
    

    # Transcribe the loaded video file into text
    # Returns the transcript as a string
    # Raises ValueError if the file is not loaded or does not exist

    def transcribe(self):
        if not self.audio_path:
            raise ValueError("Audio not extracted. Call extract_audio() first.")
        segments, _ = self.model.transcribe(self.audio_path)
        self.transcript = " ".join([segment.text for segment in segments])
        
        return self.transcript  

    # Create documents from the transcript
    # Returns a list of Document objects
    # Raises ValueError if the transcript is not available

    def create_documents(self):
        if not self.transcript:
            raise ValueError("Transcript not available. Call transcribe() first.")

        self.documents = [
            Document(
                page_content=self.transcript,
                metadata={"source": "video"}
            )
        ]

        return self.documents

    # Split the documents into chunks for further processing
    # Returns a list of text chunks
    # Raises ValueError if no documents are available

    def split_documents(self):
        if not self.documents:
            raise ValueError("No documents available. Call create_documents() first.")

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )

        self.chunks = text_splitter.split_documents(self.documents)
        return self.chunks

    # Create a vector store from the chunks
    # Returns the vector store object
    # Raises ValueError if no chunks are available

    def create_vector_store(self):
        if not self.chunks:
            raise ValueError("No chunks available. Call split_documents() first.")

        embeddings = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            google_api_key=self.api_key,
            task_type="retrieval_document"
        )

        self.vector_store = Chroma.from_documents(
            self.chunks,
            embeddings
        )
        return self.vector_store

    # Process the video file: load, transcribe, create documents, split, and create vector store
    # Returns the vector store, number of documents, and number of chunks
    # Raises RuntimeError if any step fails

    def process(self):
        try:
            os.environ["GOOGLE_API_KEY"] = self.api_key

            self.load_file()
            self.extract_audio()
            self.transcribe()
            self.create_documents()
            self.split_documents()
            self.create_vector_store()

            return self.vector_store, len(self.documents), len(self.chunks)

        except Exception as e:
            raise RuntimeError("Error processing video file") from e
            
           

        finally:
            if self.video_path and os.path.exists(self.video_path):
                os.remove(self.video_path)
            if self.audio_path and os.path.exists(self.audio_path):
                os.remove(self.audio_path)


    def __str__(self):
        return f"VideoProcessor(video_path={self.video_path}, " \
               f"chunks={'available' if self.chunks else 'not available'}, " \
               f"transcript={'available' if self.transcript else 'not available'}, " \
               f"vector_store={'available' if self.vector_store else 'not available'})"