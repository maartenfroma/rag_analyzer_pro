# Exceptions related to vector store operations.


class VectorStoreError(Exception):
    """Base class for vector store-related exceptions."""

    pass


class VectorStoreCreationError(VectorStoreError):
    """Raised when there is an error creating a vector store."""

    pass


class VectorStoreQueryError(VectorStoreError):
    """Raised when there is an error querying a vector store."""

    pass


class VectorStoreDeletionError(VectorStoreError):
    """Raised when there is an error deleting a vector store."""

    pass


class VectorStoreUpdateError(VectorStoreError):
    """Raised when there is an error updating a vector store."""

    pass


class VectorStoreConnectionError(VectorStoreError):
    """Raised when there is a connection error with a vector store."""

    pass


class VectorStoreResponseError(VectorStoreError):
    """Raised when there is a response-related error with a vector store."""

    pass


class VectorStoreTimeoutError(VectorStoreError):
    """Raised when there is a timeout error with a vector store."""

    pass


class VectorStoreNotFoundError(VectorStoreError):
    """Raised when a vector store is not found."""

    pass


class VectorSimilarityError(VectorStoreError):
    """Raised when there is a similarity-related error with a vector store."""

    pass
