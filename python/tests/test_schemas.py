"""Tests for Pydantic schemas in schemas.py."""

import pytest
from datetime import datetime, date
from pydantic import ValidationError

from src.schemas import (  # Replace 'schemas' with your actual module name
    BaseSchema,
    ObservationSchema,
    NameSchema,
    NameDescriptionSchema,
    LocationSchema,
    LocationDescriptionSchema,
    ImageSchema,
    ReviewStatus,
    SourceType,
    SCHEMAS,
)


class TestBaseSchema:
    def test_base_schema_datetime_parsing_valid(self):
        """Test BaseSchema datetime parsing with valid ISO formats."""
        valid_datetime_str = "2023-10-27T10:00:00+00:00"
        valid_datetime_z_str = "2023-10-27T10:00:00Z"  # Z notation
        schema = BaseSchema(
            created_at=valid_datetime_str, updated_at=valid_datetime_z_str
        )
        assert schema.created_at == datetime.fromisoformat(valid_datetime_str)
        assert schema.updated_at == datetime.fromisoformat(
            valid_datetime_z_str.replace("Z", "+00:00")
        )  # Z converted

    def test_base_schema_datetime_parsing_invalid(self):
        """Test BaseSchema datetime parsing with invalid format."""
        invalid_datetime_str = "2023-10-27 10:00:00"  # Space instead of T

        with pytest.raises(ValidationError) as exc_info:
            BaseSchema(created_at=invalid_datetime_str)

        errors = exc_info.value.errors(include_url=False)
        assert len(errors) == 1
        assert errors[0]["type"] == "value_error"
        assert errors[0]["loc"] == ("created_at",)
        assert "Invalid datetime format" in errors[0]["msg"]

    def test_base_schema_datetime_none(self):
        """Test BaseSchema datetime parsing with None value."""
        schema = BaseSchema(created_at=None, updated_at=None)  # Pass None values
        assert schema.created_at is None
        assert schema.updated_at is None


class TestObservationSchema:
    def test_observation_schema_date_parsing_valid(self):
        """Test ObservationSchema date parsing with valid YYYY-MM-DD format."""
        valid_date_str = "2023-10-27"
        schema = ObservationSchema(when=valid_date_str)
        assert schema.when == date(2023, 10, 27)

    def test_observation_schema_date_parsing_invalid(self):
        """Test ObservationSchema date parsing with invalid format."""
        invalid_date_str = "27-10-2023"  # DD-MM-YYYY format

        with pytest.raises(ValidationError) as exc_info:
            ObservationSchema(when=invalid_date_str)

        errors = exc_info.value.errors(include_url=False)
        assert len(errors) == 1
        assert errors[0]["type"] == "value_error"
        assert errors[0]["loc"] == ("when",)
        assert "Invalid date format" in errors[0]["msg"]

    def test_observation_schema_date_none(self):
        """Test ObservationSchema date parsing with None value."""
        schema = ObservationSchema(when=None)
        assert schema.when is None

    def test_observation_schema_lat_lng_valid(self):
        """Test ObservationSchema latitude and longitude validation with valid values."""
        schema = ObservationSchema(lat=45.0, lng=-122.5)  # Valid coordinates
        assert schema.lat == 45.0
        assert schema.lng == -122.5

    def test_observation_schema_lat_lng_invalid(self):
        """Test ObservationSchema latitude and longitude validation with invalid values."""
        with pytest.raises(ValidationError) as exc_info:
            ObservationSchema(lat=91.0, lng=-181.0)  # Invalid lat (91) and lng (-181)

        errors = exc_info.value.errors(include_url=False)
        assert len(errors) == 2  # Two validation errors
        assert any(
            err["type"] == "value_error.number.not_le" and err["loc"] == ("lat",)
            for err in errors
        )  # lat error
        assert any(
            err["type"] == "value_error.number.not_le" and err["loc"] == ("lng",)
            for err in errors
        )  # lng error
        assert (
            "Latitude must be between -90 and 90"
            in [err["msg"] for err in errors if err["loc"] == ("lat",)][0]
        )
        assert (
            "Longitude must be between -180 and 180"
            in [err["msg"] for err in errors if err["loc"] == ("lng",)][0]
        )

    def test_observation_schema_vote_cache_int_conversion_none(self):
        """Test ObservationSchema vote_cache integer validation with None and int conversion."""
        schema = ObservationSchema(vote_cache=None)  # vote_cache = None
        assert schema.vote_cache == 0  # Replaced with 0

    def test_observation_schema_vote_cache_int_conversion_valid(self):
        """Test ObservationSchema vote_cache integer validation with valid int."""
        schema = ObservationSchema(vote_cache=5)  # vote_cache = 5 (valid int)
        assert schema.vote_cache == 5  # Stays 5


class TestNameSchema:
    def test_name_schema_text_name_empty(self):
        """Test NameSchema text_name validation for empty string."""
        with pytest.raises(ValidationError) as exc_info:
            NameSchema(
                text_name="",
                search_name="search",
                display_name="display",
                sort_name="sort",
                rank=50,
            )  # Empty text_name

        errors = exc_info.value.errors(include_url=False)
        assert len(errors) == 1
        assert errors[0]["type"] == "value_error.any_str.min_length"
        assert errors[0]["loc"] == ("text_name",)
        assert "Text name must not be empty" in errors[0]["msg"]

    def test_name_schema_required_fields_missing(self):
        """Test NameSchema validation when required fields are missing."""
        with pytest.raises(ValidationError) as exc_info:
            NameSchema(
                rank=50
            )  # Missing text_name, search_name, display_name, sort_name

        errors = exc_info.value.errors(include_url=False)
        assert len(errors) == 4  # Four missing fields
        assert any(
            err["type"] == "value_error.missing" and err["loc"] == ("text_name",)
            for err in errors
        )  # text_name missing
        assert any(
            err["type"] == "value_error.missing" and err["loc"] == ("search_name",)
            for err in errors
        )  # search_name missing
        assert any(
            err["type"] == "value_error.missing" and err["loc"] == ("display_name",)
            for err in errors
        )  # display_name missing
        assert any(
            err["type"] == "value_error.missing" and err["loc"] == ("sort_name",)
            for err in errors
        )  # sort_name missing

    def test_name_schema_rank_valid(self):
        """Test NameSchema rank validation with valid rank."""
        schema = NameSchema(
            text_name="name",
            search_name="search",
            display_name="display",
            sort_name="sort",
            rank=50,
        )  # rank = 50 (valid)
        assert schema.rank == 50

    def test_name_schema_rank_invalid_range(self):
        """Test NameSchema rank validation with invalid rank range (out of bounds)."""
        with pytest.raises(ValidationError) as exc_info:
            NameSchema(
                text_name="name",
                search_name="search",
                display_name="display",
                sort_name="sort",
                rank=101,
            )  # rank = 101 (invalid - out of range)

        errors = exc_info.value.errors(include_url=False)
        assert len(errors) == 1
        assert errors[0]["type"] == "value_error.number.not_le"
        assert errors[0]["loc"] == ("rank",)
        assert "Rank must be between 1 and 100" in errors[0]["msg"]

    def test_name_schema_text_fields_none_conversion(self):
        """Test NameSchema text fields (text_name, display_name, search_name) None value conversion."""
        schema = NameSchema(
            text_name=None,
            search_name=None,
            display_name=None,
            sort_name="sort",
            rank=50,
        )  # text_name, search_name, display_name = None
        assert schema.text_name == ""  # Converted to ""
        assert schema.search_name == ""  # Converted to ""
        assert schema.display_name == ""  # Converted to ""


class TestNameDescriptionSchema:
    def test_name_description_schema_name_id_invalid(self):
        """Test NameDescriptionSchema name_id validation with invalid value (<=0)."""
        with pytest.raises(ValidationError) as exc_info:
            NameDescriptionSchema(
                name_id=0, source_type=SourceType.SYSTEM
            )  # name_id = 0 (invalid)

        errors = exc_info.value.errors(include_url=False)
        assert len(errors) == 1
        assert errors[0]["type"] == "value_error.number.not_gt"
        assert errors[0]["loc"] == ("name_id",)
        assert "Name ID must be greater than 0" in errors[0]["msg"]

    def test_name_description_schema_missing_source_type(self):
        """Test NameDescriptionSchema validation when source_type is missing."""
        with pytest.raises(ValidationError) as exc_info:
            NameDescriptionSchema(name_id=1)  # Missing source_type

        errors = exc_info.value.errors(include_url=False)
        assert len(errors) == 1
        assert errors[0]["type"] == "value_error.missing"
        assert errors[0]["loc"] == ("source_type",)
        assert "Field required" in errors[0]["msg"]

    def test_name_description_schema_review_status_default(self):
        """Test NameDescriptionSchema review_status default value."""
        schema = NameDescriptionSchema(
            name_id=1, source_type=SourceType.SYSTEM
        )  # review_status not provided
        assert (
            schema.review_status == ReviewStatus.APPROVED
        )  # Default value is APPROVED

    def test_name_description_schema_text_fields_none_conversion(self):
        """Test NameDescriptionSchema text fields (gen_desc, diag_desc, etc.) None value conversion."""
        schema = NameDescriptionSchema(
            name_id=1,
            source_type=SourceType.SYSTEM,
            gen_desc=None,
            diag_desc=None,
            look_alikes=None,
            habitat=None,
            uses=None,
            notes=None,
            refs=None,
        )  # Text fields = None
        assert schema.gen_desc == ""  # Converted to ""
        assert schema.diag_desc == ""  # Converted to ""
        assert schema.look_alikes == ""  # Converted to ""
        assert schema.habitat == ""  # Converted to ""
        assert schema.uses == ""  # Converted to ""
        assert schema.notes == ""  # Converted to ""
        assert schema.refs == ""  # Converted to ""


class TestLocationSchema:
    def test_location_schema_name_empty(self):
        """Test LocationSchema name validation for empty string."""
        with pytest.raises(ValidationError) as exc_info:
            LocationSchema(
                name="", north=45.0, south=44.0, east=-122.0, west=-123.0
            )  # name = "" (empty)

        errors = exc_info.value.errors(include_url=False)
        assert len(errors) == 1
        assert errors[0]["type"] == "value_error.any_str.min_length"
        assert errors[0]["loc"] == ("name",)
        assert "Location name must not be empty" in errors[0]["msg"]

    def test_location_schema_elevation_none_conversion(self):
        """Test LocationSchema elevation (high, low) None value conversion."""
        schema = LocationSchema(
            name="Test Location",
            north=45.0,
            south=44.0,
            east=-122.0,
            west=-123.0,
            high=None,
            low=None,
        )  # high, low = None
        assert schema.high == 0  # Converted to 0
        assert schema.low == 0  # Converted to 0


class TestLocationDescriptionSchema:
    def test_location_description_schema_location_id_invalid(self):
        """Test LocationDescriptionSchema location_id validation for invalid value (<=0)."""
        with pytest.raises(ValidationError) as exc_info:
            LocationDescriptionSchema(
                location_id=0, source_type=SourceType.SYSTEM
            )  # location_id = 0 (invalid)

        errors = exc_info.value.errors(include_url=False)
        assert len(errors) == 1
        assert errors[0]["type"] == "value_error.number.not_gt"
        assert errors[0]["loc"] == ("location_id",)
        assert "Location ID must be greater than 0" in errors[0]["msg"]

    def test_location_description_schema_missing_source_type(self):
        """Test LocationDescriptionSchema validation when source_type is missing."""
        with pytest.raises(ValidationError) as exc_info:
            LocationDescriptionSchema(location_id=1)  # Missing source_type

        errors = exc_info.value.errors(include_url=False)
        assert len(errors) == 1
        assert errors[0]["type"] == "value_error.missing"
        assert errors[0]["loc"] == ("source_type",)
        assert "Field required" in errors[0]["msg"]


class TestImageSchema:
    def test_image_schema_content_type_empty(self):
        """Test ImageSchema content_type validation for empty string."""
        with pytest.raises(ValidationError) as exc_info:
            ImageSchema(content_type="")  # content_type = "" (empty)

        errors = exc_info.value.errors(include_url=False)
        assert len(errors) == 1
        assert errors[0]["type"] == "value_error.any_str.min_length"
        assert errors[0]["loc"] == ("content_type",)
        assert "Content type must not be empty" in errors[0]["msg"]

    def test_image_schema_license_id_default(self):
        """Test ImageSchema license_id default value."""
        schema = ImageSchema(content_type="image/jpeg")  # license_id not provided
        assert schema.license_id == 10  # Default value is 10

    def test_image_schema_ok_for_export_default(self):
        """Test ImageSchema ok_for_export default value."""
        schema = ImageSchema(content_type="image/jpeg")  # ok_for_export not provided
        assert schema.ok_for_export is True  # Default value is True

    def test_image_schema_diagnostic_default(self):
        """Test ImageSchema diagnostic default value."""
        schema = ImageSchema(content_type="image/jpeg")  # diagnostic not provided
        assert schema.diagnostic is True  # Default value is True


# --- Test Schemas Dictionary ---
def test_schemas_dictionary_contains_all_schemas():
    """Test that the SCHEMAS dictionary contains all defined schemas."""
    assert "observations" in SCHEMAS
    assert "names" in SCHEMAS
    assert "name_descriptions" in SCHEMAS
    assert "locations" in SCHEMAS
    assert "location_descriptions" in SCHEMAS
    assert "images" in SCHEMAS
    assert "images_observations" in SCHEMAS
    assert "votes" in SCHEMAS
    assert "namings" in SCHEMAS
    assert "name_classifications" in SCHEMAS
    assert "herbarium_records" in SCHEMAS
    assert "observation_herbarium_records" in SCHEMAS
    assert "species" in SCHEMAS
