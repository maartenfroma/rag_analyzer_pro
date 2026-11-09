

"""Exceptions related to Gemini AI assistant."""

class GeminiError(Exception):

    """Base class for Gemini-related exceptions."""
    pass


class GeminiAuthenticationError(GeminiError):
    """Raised when there is an authentication error with Gemini."""
    pass

class GeminiModelError(GeminiError):
    """Raised when there is a model-related error with Gemini."""
    pass

class GeminiContextError(GeminiError):
    """Raised when there is a context-related error with Gemini."""
    pass

class GeminiRateLimitError(GeminiError):
    """Raised when there is a rate limit error with Gemini."""
    pass    

class GeminiResponseError(GeminiError):
    """Raised when there is a response-related error with Gemini."""
    pass    

class GeminiConnectionError(GeminiError):
    """Raised when there is a connection error with Gemini."""
    pass    