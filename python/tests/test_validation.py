"""Comprehensive Tests for data validation functions in validation.py (Combined Version)."""

import pytest
from typing import List, Optional
from pydantic import BaseModel, Field

# Import validation functions from your validation.py
from src.validation import (
    validate_species_document,
    validate_taxonomy,
    validate_location,
    validate_observation,
    validate_image,
    ValidationError,
)


# --- Test Data (Schemas and Data Samples) - Reusing and Expanding ---


class TestSchema(BaseModel):
    """Simple test schema with various data types and constraints."""

    name: str = Field(..., min_length=1)
    age: int = Field(..., ge=0)
    is_valid: bool = Field(default=True)
    optional_field: Optional[str] = None
    items: List[int] = Field(default_factory=list)


valid_data = {"name": "Test User", "age": 30, "is_valid": True, "items": [1, 2, 3]}
invalid_data_missing_field = {"age": 30, "is_valid": True}  # Missing 'name' (required)
invalid_data_wrong_type = {
    "name": "Test User",
    "age": "invalid",
    "is_valid": True,
}  # 'age' should be int
invalid_data_validation_error = {
    "name": "",
    "age": -1,
    "is_valid": True,
}  # 'name' too short, 'age' negative

# --- Additional Test Data ---

valid_data_nested = {
    "name": "Test User",
    "age": 25,
    "is_valid": True,
    "items": [1, 2],
    "nested": {"field1": "value1", "field2": 42},
}

valid_data_array = {
    "name": "Test User",
    "age": 35,
    "is_valid": True,
    "items": [1, 2, 3, 4, 5],
    "array_field": ["a", "b", "c"],
}

invalid_data_nested = {
    "name": "Test User",
    "age": 25,
    "is_valid": True,
    "items": [1, 2],
    "nested": "not_an_object",  # Should be object
}

invalid_data_array = {
    "name": "Test User",
    "age": 35,
    "is_valid": True,
    "items": [1, "2", 3],  # Mixed types not allowed
    "array_field": ["a", 2, "c"],
}

# --- New Schema Classes ---


class NestedSchema(BaseModel):
    """Schema with nested objects and arrays."""

    name: str
    nested: dict = Field(..., description="Nested object")
    array: List[str] = Field(default_factory=list)


class ConstrainedSchema(BaseModel):
    """Schema with additional constraints."""

    id: int = Field(..., gt=0)
    name: str = Field(..., min_length=2, max_length=50)
    score: float = Field(..., ge=0.0, le=100.0)
    tags: List[str] = Field(..., min_items=1)


# --- Additional Test Cases ---


class TestSchemaValidationExtended:
    """Additional test cases for schema validation."""

    def test_nested_schema_validation(self):
        """Test validation of nested schema structures."""
        schema = NestedSchema
        valid_nested = {
            "name": "test",
            "nested": {"key": "value"},
            "array": ["item1", "item2"],
        }
        assert validate_data(valid_nested, schema) is True

    def test_constrained_schema_validation(self):
        """Test validation with additional constraints."""
        schema = ConstrainedSchema
        valid_constrained = {"id": 1, "name": "test", "score": 75.5, "tags": ["tag1"]}
        assert validate_data(valid_constrained, schema) is True

        invalid_constrained = {
            "id": 0,  # Should be > 0
            "name": "t",  # Too short
            "score": 101,  # Too high
            "tags": [],  # Empty list not allowed
        }
        assert validate_data(invalid_constrained, schema) is False

    def test_array_validation(self):
        """Test validation of array fields."""
        schema = {
            "type": "object",
            "properties": {
                "items": {"type": "array", "items": {"type": "integer"}, "minItems": 1}
            },
        }
        assert validate_data({"items": [1, 2, 3]}, schema) is True
        assert validate_data({"items": []}, schema) is False
        assert validate_data({"items": ["1", "2"]}, schema) is False

    def test_complex_nested_validation(self):
        """Test validation of complex nested structures."""
        schema = {
            "type": "object",
            "properties": {
                "nested": {
                    "type": "object",
                    "properties": {
                        "array": {"type": "array", "items": {"type": "string"}}
                    },
                }
            },
        }
        valid_complex = {"nested": {"array": ["a", "b", "c"]}}
        assert validate_data(valid_complex, schema) is True

    """Simple test schema with various data types and constraints."""

    name: str = Field(..., min_length=1)
    age: int = Field(..., ge=0)
    is_valid: bool = Field(default=True)
    optional_field: Optional[str] = None
    items: List[int] = Field(default_factory=list)


valid_data = {"name": "Test User", "age": 30, "is_valid": True, "items": [1, 2, 3]}
invalid_data_missing_field = {"age": 30, "is_valid": True}  # Missing 'name' (required)
invalid_data_wrong_type = {
    "name": "Test User",
    "age": "invalid",
    "is_valid": True,
}  # 'age' should be int
invalid_data_validation_error = {
    "name": "",
    "age": -1,
    "is_valid": True,
}  # 'name' too short, 'age' negative
invalid_data_constraint_violation = {
    "name": "Test",
    "age": 0,
    "is_valid": "maybe",
}  # 'is_valid' should be bool
valid_data_with_optional = {
    "name": "Test User",
    "age": 30,
    "is_valid": True,
    "optional_field": "optional value",
}
valid_data_empty_list = {"name": "Test User", "age": 30, "is_valid": True, "items": []}
invalid_data_list_wrong_type = {
    "name": "Test User",
    "age": 30,
    "is_valid": True,
    "items": ["a", "b"],
}


@pytest.fixture
def sample_json_schema_dict():
    """Fixture for a sample JSON schema dictionary."""
    return {
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "name": {"type": "string"},
            "location": {
                "type": "object",
                "properties": {
                    "lat": {"type": "number", "minimum": -90, "maximum": 90},
                    "lng": {"type": "number", "minimum": -180, "maximum": 180},
                },
                "required": ["lat", "lng"],
            },
        },
        "required": ["id", "name"],
    }


# --- Test Functions - Combined and Enhanced ---


class TestValidationFunctionsCombined:  # Combined test class
    # --- to_json_schema Tests ---
    def test_to_json_schema_valid(self):
        """Test to_json_schema function with a valid Pydantic model."""
        schema = to_json_schema(TestSchema)
        assert isinstance(schema, dict)
        assert schema["title"] == "TestSchema"
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "name" in schema["properties"]
        assert "age" in schema["properties"]
        assert "is_valid" in schema["properties"]
        assert (
            schema["properties"]["name"]["minLength"] == 1
        )  # Check for constraint from Field
        assert (
            schema["properties"]["age"]["minimum"] == 0
        )  # Check for constraint from Field

    # --- validate_data Tests ---
    class TestValidateData:  # Nested class for validate_data tests
        def test_validate_data_valid_data_json_schema(self, sample_json_schema_dict):
            """Test validate_data function with valid data against a JSON schema."""
            assert (
                validate_data(valid_data, sample_json_schema_dict) is True
            )  # Valid data, JSON schema dict

        def test_validate_data_valid_data_pydantic_schema_class(self):
            """Test validate_data function with valid data against a Pydantic schema class."""
            assert (
                validate_data(valid_data, TestSchema) is True
            )  # Valid data, Pydantic schema class

        def test_validate_data_invalid_data_missing_field(
            self, sample_json_schema_dict
        ):
            """Test validate_data function with invalid data (missing required field)."""
            assert (
                validate_data(invalid_data_missing_field, sample_json_schema_dict)
                is False
            )  # Missing 'name' should fail

        def test_validate_data_invalid_data_wrong_type(self, sample_json_schema_dict):
            """Test validate_data function with invalid data (wrong data type)."""
            assert (
                validate_data(invalid_data_wrong_type, sample_json_schema_dict) is False
            )  # Wrong type for 'age' should fail

        def test_validate_data_invalid_data_validation_error(
            self, sample_json_schema_dict
        ):
            """Test validate_data function with invalid data (validation error - min_length, ge)."""
            assert (
                validate_data(invalid_data_validation_error, sample_json_schema_dict)
                is False
            )  # Validation errors should fail

        def test_validate_data_invalid_schema_type(self, sample_json_schema_dict):
            """Test validate_data function with an invalid schema (not a dict)."""
            invalid_schema = "not a schema"  # Invalid schema type
            assert (
                validate_data(valid_data, invalid_schema) is False
            )  # Invalid schema should fail

        def test_validate_data_exception_handling(self, sample_json_schema_dict):
            """Test validate_data function exception handling during validation."""
            # Simulate a schema that causes an exception during validation
            faulty_schema = {
                "type": "object",
                "properties": {"name": {"type": "integer"}},
            }  # Schema expects int, data is string
            assert (
                validate_data(valid_data, faulty_schema) is False
            )  # Validation exception should be caught, return False

        def test_validate_data_none_values_allowed_in_schema(self):
            """Test validate_data function with None values when allowed in schema."""
            schema = {
                "type": "object",
                "properties": {"field": {"type": ["string", "null"]}},
            }
            data = {"field": None}
            assert (
                validate_data(data, schema) is True
            )  # None allowed by schema, should pass

        def test_validate_data_valid_optional_field(self, sample_json_schema_dict):
            """Test validate_data function with valid data including optional field."""
            assert (
                validate_data(valid_data_with_optional, to_json_schema(TestSchema))
                is True
            )  # Optional field present, should pass

        def test_validate_data_valid_empty_list_field(self, sample_json_schema_dict):
            """Test validate_data function with valid data including empty list field."""
            assert (
                validate_data(valid_data_empty_list, to_json_schema(TestSchema)) is True
            )  # Empty list for list field, should pass

        def test_validate_data_invalid_list_wrong_type(self, sample_json_schema_dict):
            """Test validate_data function with invalid data - list field with wrong type items."""
            assert (
                validate_data(invalid_data_list_wrong_type, to_json_schema(TestSchema))
                is False
            )  # List with wrong type items, should fail


"""Tests for data validation after pipeline processing."""
import pytest

from validation import (
    validate_species_document,
    validate_taxonomy,
    validate_location,
    validate_observation,
    validate_image,
    ValidationError,
)
from config import DataConfig


@pytest.fixture
def validation_config(tmp_path):
    """Create test configuration for validation tests."""
    return DataConfig(
        DATA_DIR=str(tmp_path),
        MONGODB_URI="mongodb://localhost:27017",
        DATABASE_NAME="test_mushroom_validation",
        BATCH_SIZE=100,
        NULL_VALUES=("", "NA", "N/A", "NULL", "NaN", "None"),
    )


@pytest.fixture
def sample_species_document():
    """Create a sample species document for testing."""
    return {
        "_id": 1,
        "scientific_name": "Amanita muscaria",
        "author": "L.) Lam.",
        "rank": 20,
        "deprecated": False,
        "classification": {
            "kingdom": "Fungi",
            "phylum": "Basidiomycota",
            "class": "Agaricomycetes",
            "order": "Agaricales",
            "family": "Amanitaceae",
            "genus": "Amanita",
            "taxonomic_completeness": 1.0,
        },
        "descriptions": {
            "general": "Red cap with white spots",
            "diagnostic": "Distinctive red cap",
            "distribution": "Widespread",
            "habitat": "Under conifers",
            "look_alikes": "None known",
            "uses": "Medicinal",
            "notes": "Iconic mushroom",
            "sources": [{"source_type": 0, "source_name": "System"}],
        },
        "observations": {
            "observation_count": 2,
            "vote_stats": {"min": 1.5, "max": 2.5, "avg": 2.0},
            "observations": [
                {
                    "id": 1,
                    "when": "2023-01-01",
                    "location_name": "Test Forest",
                    "lat": 45.5,
                    "lng": -122.5,
                    "alt": 150,
                    "vote_cache": 1.5,
                    "is_collection_location": True,
                }
            ],
        },
        "location_data": [
            {
                "name": "Test Forest",
                "north": 45.5,
                "south": 45.4,
                "east": -122.5,
                "west": -122.6,
                "elevation": "100-200m",
                "continent": "North America",
                "ecology": "Temperate rainforest",
            }
        ],
        "images": [
            {
                "image_id": 1,
                "content_type": "image/jpeg",
                "copyright_holder": "User 1",
                "license_id": 1,
                "ok_for_export": True,
                "diagnostic": True,
                "width": 800,
                "height": 600,
                "rank": 1,
            }
        ],
        "synonyms": [
            {"id": 3, "name": "Synonym Name", "author": "Author 3", "rank": 4}
        ],
    }


class TestSpeciesDocumentValidation:
    def test_valid_species_document(self, sample_species_document):
        """Test validation of a valid species document."""
        # Should not raise any validation errors
        validate_species_document(sample_species_document)

    def test_invalid_species_document(self, sample_species_document):
        """Test validation with invalid species document."""
        # Remove required field
        del sample_species_document["scientific_name"]

        with pytest.raises(ValidationError):
            validate_species_document(sample_species_document)

    def test_empty_species_document(self):
        """Test validation with empty document."""
        with pytest.raises(ValidationError):
            validate_species_document({})

    def test_species_document_data_types(self, sample_species_document):
        """Test validation of data types in species document."""
        # Test invalid rank type
        sample_species_document["rank"] = "invalid"
        with pytest.raises(ValidationError):
            validate_species_document(sample_species_document)

        # Test invalid deprecated type
        sample_species_document["rank"] = 20  # Fix rank
        sample_species_document["deprecated"] = "true"  # Should be boolean
        with pytest.raises(ValidationError):
            validate_species_document(sample_species_document)


class TestTaxonomyValidation:
    def test_valid_taxonomy(self):
        """Test validation of valid taxonomy."""
        taxonomy = {
            "kingdom": "Fungi",
            "phylum": "Basidiomycota",
            "class": "Agaricomycetes",
            "order": "Agaricales",
            "family": "Amanitaceae",
            "genus": "Amanita",
            "taxonomic_completeness": 1.0,
        }

        # Should not raise any validation errors
        validate_taxonomy(taxonomy)

    def test_invalid_taxonomy(self):
        """Test validation with invalid taxonomy."""
        taxonomy = {
            "kingdom": "Invalid",  # Invalid kingdom
            "phylum": "",  # Empty value
            "class": None,  # Missing value
            "order": "Agaricales",
            "family": "Amanitaceae",
            "genus": "Amanita",
            "taxonomic_completeness": 0.5,
        }

        with pytest.raises(ValidationError):
            validate_taxonomy(taxonomy)

    def test_missing_required_ranks(self):
        """Test validation with missing required taxonomic ranks."""
        taxonomy = {
            "kingdom": "Fungi",
            # Missing phylum and class
            "order": "Agaricales",
            "family": "Amanitaceae",
            "genus": "Amanita",
        }

        with pytest.raises(ValidationError):
            validate_taxonomy(taxonomy)


class TestLocationValidation:
    def test_valid_location(self):
        """Test validation of valid location."""
        location = {
            "name": "Test Forest",
            "north": 45.5,
            "south": 45.4,
            "east": -122.5,
            "west": -122.6,
            "elevation": "100-200m",
            "continent": "North America",
            "ecology": "Temperate rainforest",
        }

        # Should not raise any validation errors
        validate_location(location)

    def test_invalid_coordinates(self):
        """Test validation with invalid coordinates."""
        location = {
            "name": "Test Forest",
            "north": 91.0,  # Invalid latitude
            "south": 45.4,
            "east": -182.0,  # Invalid longitude
            "west": -122.6,
            "elevation": "100-200m",
        }

        with pytest.raises(ValidationError):
            validate_location(location)

    def test_invalid_elevation(self):
        """Test validation with invalid elevation format."""
        location = {
            "name": "Test Forest",
            "north": 45.5,
            "south": 45.4,
            "east": -122.5,
            "west": -122.6,
            "elevation": "invalid",  # Invalid elevation format
        }

        with pytest.raises(ValidationError):
            validate_location(location)


class TestObservationValidation:
    def test_valid_observation(self):
        """Test validation of valid observation."""
        observation = {
            "id": 1,
            "when": "2023-01-01",
            "location_name": "Test Forest",
            "lat": 45.5,
            "lng": -122.5,
            "alt": 150,
            "vote_cache": 1.5,
            "is_collection_location": True,
        }

        # Should not raise any validation errors
        validate_observation(observation)

    def test_invalid_date(self):
        """Test validation with invalid date format."""
        observation = {
            "id": 1,
            "when": "invalid",  # Invalid date format
            "location_name": "Test Forest",
            "lat": 45.5,
            "lng": -122.5,
        }

        with pytest.raises(ValidationError):
            validate_observation(observation)

    def test_invalid_coordinates(self):
        """Test validation with invalid coordinates."""
        observation = {
            "id": 1,
            "when": "2023-01-01",
            "location_name": "Test Forest",
            "lat": 91.0,  # Invalid latitude
            "lng": -182.0,  # Invalid longitude
        }

        with pytest.raises(ValidationError):
            validate_observation(observation)


class TestImageValidation:
    def test_valid_image(self):
        """Test validation of valid image."""
        image = {
            "image_id": 1,
            "content_type": "image/jpeg",
            "copyright_holder": "User 1",
            "license_id": 1,
            "ok_for_export": True,
            "diagnostic": True,
            "width": 800,
            "height": 600,
            "rank": 1,
        }

        # Should not raise any validation errors
        validate_image(image)

    def test_invalid_content_type(self):
        """Test validation with invalid content type."""
        image = {
            "image_id": 1,
            "content_type": "invalid",  # Invalid content type
            "copyright_holder": "User 1",
            "license_id": 1,
        }

        with pytest.raises(ValidationError):
            validate_image(image)

    def test_invalid_dimensions(self):
        """Test validation with invalid image dimensions."""
        image = {
            "image_id": 1,
            "content_type": "image/jpeg",
            "copyright_holder": "User 1",
            "license_id": 1,
            "width": -1,  # Invalid width
            "height": 0,  # Invalid height
        }

        with pytest.raises(ValidationError):
            validate_image(image)


class TestDataQualityValidation:
    def test_taxonomic_completeness(self, sample_species_document):
        """Test validation of taxonomic completeness."""
        taxonomy = sample_species_document["classification"]

        # Test with complete taxonomy
        assert taxonomy["taxonomic_completeness"] == 1.0

        # Test with incomplete taxonomy
        del taxonomy["class"]
        del taxonomy["order"]
        taxonomy["taxonomic_completeness"] = len(taxonomy) / 7  # 7 possible ranks

        with pytest.raises(ValidationError):
            validate_taxonomy(taxonomy)

    def test_description_quality(self, sample_species_document):
        """Test validation of description quality."""
        descriptions = sample_species_document["descriptions"]

        # Test with good quality descriptions
        assert len(descriptions["general"]) > 10
        assert len(descriptions["diagnostic"]) > 10

        # Test with poor quality description
        descriptions["general"] = "Short"
        descriptions["diagnostic"] = ""

        with pytest.raises(ValidationError):
            validate_species_document(sample_species_document)

    def test_observation_completeness(self, sample_species_document):
        """Test validation of observation completeness."""
        observations = sample_species_document["observations"]

        # Test with complete observation data
        assert observations["observation_count"] > 0
        assert len(observations["observations"]) > 0

        # Test with incomplete observation
        incomplete_observation = {
            "id": 2,
            "when": "2023-01-01",
            # Missing location and coordinates
        }
        observations["observations"].append(incomplete_observation)

        with pytest.raises(ValidationError):
            validate_species_document(sample_species_document)

    def test_image_metadata_completeness(self, sample_species_document):
        """Test validation of image metadata completeness."""
        images = sample_species_document["images"]

        # Test with complete image metadata
        assert all("content_type" in img for img in images)
        assert all("copyright_holder" in img for img in images)
        assert all("license_id" in img for img in images)

        # Test with incomplete image metadata
        incomplete_image = {
            "image_id": 2,
            "content_type": "image/jpeg",
            # Missing copyright and license info
        }
        images.append(incomplete_image)

        with pytest.raises(ValidationError):
            validate_species_document(sample_species_document)
