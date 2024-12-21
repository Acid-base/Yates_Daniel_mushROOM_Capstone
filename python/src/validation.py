"""Enhanced data validation utilities."""

from typing import Any, Dict, Protocol, List, Optional
from dataclasses import dataclass
from datetime import datetime
import re

from exceptions import ValidationError

class Validator(Protocol):
    """Protocol for data validators."""
    def validate(self, data: Any) -> bool:
        """Validate data and return True if valid."""
        ...

@dataclass
class ValidationResult:
    """Container for validation results."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]

class SchemaValidator:
    """Validates data against a schema with custom rules."""
    
    def __init__(self, schema: Dict[str, type]):
        self.schema = schema
    
    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        """Validate data against schema."""
        errors = []
        warnings = []
        
        # Check required fields
        for field, field_type in self.schema.items():
            if field not in data:
                errors.append(f"Missing required field: {field}")
                continue
                
            value = data[field]
            if value is not None and not isinstance(value, field_type):
                errors.append(
                    f"Invalid type for {field}: expected {field_type.__name__}, "
                    f"got {type(value).__name__}"
                )
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

class DateValidator:
    """Validates date fields."""
    
    def __init__(self, date_format: str = "%Y-%m-%d"):
        self.date_format = date_format
    
    def validate(self, date_str: str) -> ValidationResult:
        """Validate date string."""
        errors = []
        warnings = []
        
        try:
            datetime.strptime(date_str, self.date_format)
        except ValueError as e:
            errors.append(f"Invalid date format: {str(e)}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

class LocationValidator:
    """Validates location data."""
    
    def validate(self, location: Dict[str, Any]) -> ValidationResult:
        """Validate location data."""
        errors = []
        warnings = []
        
        # Validate coordinates
        lat = location.get("lat")
        lng = location.get("lng")
        
        if lat is not None and not -90 <= lat <= 90:
            errors.append(f"Invalid latitude: {lat}")
        
        if lng is not None and not -180 <= lng <= 180:
            errors.append(f"Invalid longitude: {lng}")
        
        # Validate elevation if present
        alt = location.get("alt")
        if alt is not None and alt < -500:  # Assuming Dead Sea is lowest point
            warnings.append(f"Unusually low elevation: {alt}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

class NameValidator:
    """Validates scientific names."""
    
    def __init__(self):
        # Basic pattern for scientific names (Genus species)
        self.name_pattern = re.compile(r'^[A-Z][a-z]+ [a-z]+$')
    
    def validate(self, name: str) -> ValidationResult:
        """Validate scientific name."""
        errors = []
        warnings = []
        
        if not self.name_pattern.match(name):
            warnings.append(
                f"Name '{name}' may not follow scientific naming conventions"
            )
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

def validate_with_schema(
    data: Dict[str, Any],
    schema: Dict[str, type],
    validators: Optional[List[Validator]] = None
) -> ValidationResult:
    """Validate data with schema and optional custom validators."""
    schema_validator = SchemaValidator(schema)
    schema_result = schema_validator.validate(data)
    
    if not schema_result.is_valid:
        return schema_result
    
    if not validators:
        return schema_result
    
    all_errors = schema_result.errors
    all_warnings = schema_result.warnings
    
    for validator in validators:
        result = validator.validate(data)
        all_errors.extend(result.errors)
        all_warnings.extend(result.warnings)
    
    return ValidationResult(
        is_valid=len(all_errors) == 0,
        errors=all_errors,
        warnings=all_warnings
    ) 

def validate_data(data: Dict[str, Any], schema: Dict[str, type]) -> bool:
    """Validate data against schema."""
    try:
        result = validate_with_schema(data, schema)
        return result.is_valid
    except Exception as e:
        return False 