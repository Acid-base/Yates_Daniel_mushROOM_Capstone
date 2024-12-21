"""Custom exceptions for the data processing pipeline."""


class DataProcessingError(Exception):
    """Base exception for data processing errors."""

    pass


class FileProcessingError(DataProcessingError):
    """Raised when file processing fails."""

    pass


class ValidationError(DataProcessingError):
    """Raised when data validation fails."""

    def __init__(self, message: str, field: str | None = None):
        self.field = field
        super().__init__(message)


class DatabaseError(DataProcessingError):
    """Raised when database operations fail."""

    def __init__(self, message: str, operation: str | None = None):
        self.operation = operation
        super().__init__(message)


class APIError(DataProcessingError):
    """Raised when API operations fail."""

    def __init__(self, message: str, status_code: int | None = None):
        self.status_code = status_code
        super().__init__(message)


class RateLimitError(APIError):
    """Raised when API rate limits are exceeded."""

    def __init__(self, retry_after: int | None = None):
        self.retry_after = retry_after
        super().__init__("Rate limit exceeded")


class ConfigurationError(DataProcessingError):
    """Raised when configuration is invalid or missing."""

    pass
