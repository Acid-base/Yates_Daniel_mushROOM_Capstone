"""Custom exceptions for the data processing pipeline."""

class DataProcessingError(Exception):
    """Base exception for data processing errors."""
    pass

class ValidationError(DataProcessingError):
    """Raised when data validation fails."""
    pass

class DatabaseError(DataProcessingError):
    """Raised when database operations fail."""
    pass

class ConfigurationError(DataProcessingError):
    """Raised when configuration is invalid or missing."""
    pass

class FileProcessingError(DataProcessingError):
    """Raised when file processing fails."""
    pass 