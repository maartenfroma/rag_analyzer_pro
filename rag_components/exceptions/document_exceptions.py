# Document-related exceptions for the RAG components.


class DocumentError(Exception):
    """Base class for document-related exceptions."""

    pass


class UnsupportedDocumentException(DocumentError):
    """Raised when the document has an unsupported file extension."""

    pass


class DocumentLoadError(DocumentError):
    """Raised when there is an error loading a document."""

    pass


class DocumentFileError(DocumentError):
    """Raised when there is an error with the document file."""

    pass


class DocumentSplitError(DocumentError):
    """Raised when there is an error splitting a document."""

    pass


class DocumentSaveError(DocumentError):
    """Raised when there is an error saving a document."""

    pass


class DocumentNotFoundError(DocumentError):
    """Raised when a document is not found."""

    pass


class DocumentUpdateError(DocumentError):
    """Raised when there is an error updating a document."""

    pass


class DocumentPermissionError(DocumentError):
    """Raised when there is a permission-related error with a document."""

    pass


class DocumentTimeoutError(DocumentError):
    """Raised when there is a timeout error with a document."""

    pass


class DocumentConnectionError(DocumentError):
    """Raised when there is a connection error with a document."""

    pass


class DocumentResponseError(DocumentError):
    """Raised when there is a response-related error with a document."""

    pass


class DocumentValidationError(DocumentError):
    """Raised when there is a validation-related error with a document."""

    pass


class ProcessorCreationError(DocumentError):
    """Raised when there is an error creating a processor."""

    pass
