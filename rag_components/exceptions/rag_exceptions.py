
class RAGEngineError(Exception):
    """Base class for all RAG-related exceptions."""
    pass

class VectorStoreError(RAGEngineError):
    """Exception raised for errors related to the vector store."""
    pass

class SimilaritySearchError(RAGEngineError):
    """Exception raised for errors during similarity search in the vector store."""
    pass    

class ContextGenerationError(RAGEngineError):
    """Exception raised for errors during context generation."""
    pass