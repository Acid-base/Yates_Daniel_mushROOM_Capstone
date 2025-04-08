"""Tests for custom exceptions."""

from exceptions import (
    DataProcessingError,
    FileProcessingError,
    ValidationError,
    DatabaseError,
    APIError,
    RateLimitError,
    ConfigurationError,
)


def test_data_processing_error():
    """Test DataProcessingError."""
    error = DataProcessingError("Test error")
    assert str(error) == "Test error"
    assert isinstance(error, Exception)


def test_file_processing_error():
    """Test FileProcessingError."""
    error = FileProcessingError("File error")
    assert str(error) == "File error"
    assert isinstance(error, DataProcessingError)


def test_validation_error():
    """Test ValidationError with field."""
    error = ValidationError("Invalid data", field="test_field")
    assert str(error) == "Invalid data"
    assert error.field == "test_field"
    assert isinstance(error, DataProcessingError)


def test_validation_error_without_field():
    """Test ValidationError without field."""
    error = ValidationError("Invalid data")
    assert str(error) == "Invalid data"
    assert error.field is None
    assert isinstance(error, DataProcessingError)


def test_database_error():
    """Test DatabaseError with operation."""
    error = DatabaseError("Database connection failed", operation="connect")
    assert str(error) == "Database connection failed"
    assert error.operation == "connect"
    assert isinstance(error, DataProcessingError)


def test_database_error_without_operation():
    """Test DatabaseError without operation."""
    error = DatabaseError("Database error")
    assert str(error) == "Database error"
    assert error.operation is None
    assert isinstance(error, DataProcessingError)


def test_api_error():
    """Test APIError with status code."""
    error = APIError("API request failed", status_code=404)
    assert str(error) == "API request failed"
    assert error.status_code == 404
    assert isinstance(error, DataProcessingError)


def test_api_error_without_status_code():
    """Test APIError without status code."""
    error = APIError("API error")
    assert str(error) == "API error"
    assert error.status_code is None
    assert isinstance(error, DataProcessingError)


def test_rate_limit_error():
    """Test RateLimitError with retry_after."""
    error = RateLimitError(retry_after=60)
    assert str(error) == "Rate limit exceeded"
    assert error.retry_after == 60
    assert isinstance(error, APIError)


def test_rate_limit_error_without_retry_after():
    """Test RateLimitError without retry_after."""
    error = RateLimitError()
    assert str(error) == "Rate limit exceeded"
    assert error.retry_after is None
    assert isinstance(error, APIError)


def test_configuration_error():
    """Test ConfigurationError."""
    error = ConfigurationError("Missing configuration")
    assert str(error) == "Missing configuration"
    assert isinstance(error, DataProcessingError)
