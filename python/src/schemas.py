"""Pydantic schemas for data validation - Finalized based on MySQL schema and API/CSV data."""

from typing import Dict, Optional, Any, List, Type, TypeVar
from datetime import datetime, date
from pydantic import BaseModel, Field, field_validator
from enum import Enum
import warnings
from pydantic.json_schema import PydanticJsonSchemaWarning

# Suppress the specific Pydantic warning about non-serializable defaults
warnings.filterwarnings("ignore", category=PydanticJsonSchemaWarning)

# Define a type variable for model types
T = TypeVar("T", bound=BaseModel)


# Add validate_record function that's needed by the test_pipeline.py
def validate_record(data: Dict[str, Any], schema_class: Type[T]) -> T:
    """Validate a record against a Pydantic schema.

    Args:
        data: The data dictionary to validate
        schema_class: The Pydantic schema class to validate against

    Returns:
        An instance of the schema class with validated data

    Raises:
        ValidationError: If validation fails
    """
    # Create an instance of the schema with the data
    return schema_class.model_validate(data)


class ReviewStatus(Enum):
    PENDING = 0
    APPROVED = 1
    REJECTED = 2


class SourceType(Enum):
    USER = 0
    SYSTEM = 1


class BaseSchema(BaseModel):
    """Base schema with common fields."""

    id: Optional[int] = None
    created_at: Optional[datetime] = None  # Changed to Optional and defaulted to None
    updated_at: Optional[datetime] = None  # Changed to Optional and defaulted to None

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def parse_datetime(cls, value):
        if value is None:  # Allow None values to pass validation
            return None
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                raise ValueError(
                    f"Invalid datetime format: {value}. Expected ISO format (YYYY-MM-DDTHH:MM:SSZ or YYYY-MM-DDTHH:MM:SS+HH:MM)."
                )
        return value


class ObservationSchema(BaseSchema):
    """Schema for the 'observations' table."""

    when: Optional[date] = None  # Changed to date and Optional
    user_id: Optional[int] = None
    specimen: bool = False
    notes: Optional[str] = None
    thumb_image_id: Optional[int] = None
    name_id: Optional[int] = None
    location_id: Optional[int] = None
    is_collection_location: bool = Field(default=True)
    vote_cache: Optional[float] = None
    lat: Optional[float] = Field(
        None, ge=-90, le=90, description="Latitude must be between -90 and 90."
    )
    lng: Optional[float] = Field(
        None, ge=-180, le=180, description="Longitude must be between -180 and 180."
    )
    alt: Optional[int] = None
    gps_hidden: bool = Field(default=False)
    needs_naming: bool = Field(default=False)
    location_lat: Optional[float] = Field(
        None, ge=-90, le=90, description="Location latitude must be between -90 and 90."
    )
    location_lng: Optional[float] = Field(
        None,
        ge=-180,
        le=180,
        description="Location longitude must be between -180 and 180.",
    )
    where: Optional[str] = None  # Added from MySQL schema
    lifeform: Optional[str] = None  # Added from MySQL schema
    text_name: Optional[str] = None  # Added from MySQL schema
    classification: Optional[str] = None  # Added from MySQL schema
    source: Optional[int] = None  # Added from MySQL schema
    log_updated_at: Optional[datetime] = None  # Added from MySQL schema
    inat_id: Optional[int] = None  # Added from MySQL schema
    rss_log_id: Optional[int] = None  # Added from MySQL schema
    num_views: int = Field(default=0)  # Added from MySQL schema, default 0
    last_view: Optional[datetime] = None  # Added from MySQL schema

    @field_validator("when", mode="before")
    @classmethod
    def parse_when_date(cls, value):  # Changed to parse_when_date and date type
        if value is None:  # Allow None values to pass validation
            return None
        if isinstance(value, str):
            try:
                return datetime.strptime(value, "%Y-%m-%d").date()  # Parse as date
            except ValueError:
                raise ValueError(f"Invalid date format: {value}. Expected YYYY-MM-DD.")
        return value

    @field_validator(
        "vote_cache", "specimen", "location_id", "thumb_image_id", "name_id"
    )
    @classmethod
    def validate_integers(cls, v):
        if v is None:
            return 0
        return v


class NameSchema(BaseSchema):
    """Schema for the 'names' table."""

    text_name: str = Field(
        ..., min_length=1, description="Text name must not be empty."
    )
    search_name: str = Field(
        ..., min_length=1, description="Search name must not be empty."
    )
    display_name: str = Field(
        ..., min_length=1, description="Display name must not be empty."
    )
    sort_name: str = Field(
        ..., min_length=1, description="Sort name must not be empty."
    )
    author: Optional[str] = None
    citation: Optional[str] = None
    deprecated: bool = Field(default=False)
    synonym_id: Optional[int] = None
    correct_spelling_id: Optional[int] = None
    rank: int = Field(..., ge=1, le=100, description="Rank must be between 1 and 100")
    notes: Optional[str] = None
    classification: Optional[str] = None
    ok_for_export: bool = Field(default=True)
    lifeform: Optional[str] = Field(default=" ")  # Default value from MySQL schema
    locked: bool = Field(default=False)
    description_id: Optional[int] = None  # Added from MySQL schema
    rss_log_id: Optional[int] = None  # Added from MySQL schema
    num_views: int = Field(default=0)  # Added from MySQL schema, default 0
    last_view: Optional[datetime] = None  # Added from MySQL schema
    icn_id: Optional[int] = None  # Added from MySQL schema
    user_id: Optional[int] = (
        None  # Added from MySQL schema (though likely should be Required in some contexts)
    )

    @field_validator("text_name", "display_name", "search_name")
    @classmethod
    def validate_text_fields(cls, v):
        if v is None:
            return ""
        return v


class NameDescriptionSchema(BaseSchema):
    """Schema for the 'name_descriptions' table."""

    user_id: Optional[int] = None
    name_id: int = Field(..., gt=0, description="Name ID must be greater than 0.")
    review_status: ReviewStatus = Field(
        default=ReviewStatus.APPROVED
    )  # Default from MySQL
    source_type: SourceType
    source_name: Optional[str] = None
    public: Optional[bool] = None
    locale: Optional[str] = None
    license_id: Optional[int] = None
    gen_desc: Optional[str] = None
    diag_desc: Optional[str] = None
    distribution: Optional[str] = None
    habitat: Optional[str] = None
    look_alikes: Optional[str] = None
    uses: Optional[str] = None
    notes: Optional[str] = None
    refs: Optional[str] = None
    classification: Optional[str] = None
    version: Optional[int] = None  # Added from MySQL schema
    last_review: Optional[datetime] = None  # Added from MySQL schema
    reviewer_id: Optional[int] = None  # Added from MySQL schema
    ok_for_export: bool = Field(default=True)  # Default from MySQL schema
    num_views: int = Field(default=0)  # Added from MySQL schema, default 0
    last_view: Optional[datetime] = None  # Added from MySQL schema
    project_id: Optional[int] = None  # Added from MySQL schema

    @field_validator(
        "gen_desc", "diag_desc", "look_alikes", "habitat", "uses", "notes", "refs"
    )
    @classmethod
    def validate_text_fields(cls, v):
        if v is None:
            return ""
        return v


class LocationSchema(BaseSchema):
    """Schema for the 'locations' table."""

    user_id: Optional[int] = None
    name: str = Field(..., min_length=1, description="Location name must not be empty.")
    north: float
    south: float
    west: float
    east: float
    high: Optional[float] = None
    low: Optional[float] = None
    notes: Optional[str] = None
    scientific_name: Optional[str] = None
    locked: bool = Field(default=False)
    hidden: bool = Field(default=False)
    version: Optional[int] = None  # Added from MySQL schema
    description_id: Optional[int] = None  # Added from MySQL schema
    rss_log_id: Optional[int] = None  # Added from MySQL schema
    num_views: int = Field(default=0)  # Added from MySQL schema, default 0
    last_view: Optional[datetime] = None  # Added from MySQL schema
    ok_for_export: bool = Field(default=True)  # Added from MySQL schema
    box_area: Optional[float] = None  # Added from MySQL schema (decimal to float)
    center_lat: Optional[float] = None  # Added from MySQL schema (decimal to float)
    center_lng: Optional[float] = None  # Added from MySQL schema (decimal to float)

    @field_validator("high", "low")
    @classmethod
    def validate_elevation(cls, v):
        if v is None:
            return 0
        return v


class LocationDescriptionSchema(BaseSchema):
    """Schema for the 'location_descriptions' table."""

    user_id: Optional[int] = None
    location_id: int = Field(
        ..., gt=0, description="Location ID must be greater than 0."
    )
    source_type: SourceType
    source_name: Optional[str] = None
    public: Optional[bool] = None
    locale: Optional[str] = None
    license_id: Optional[int] = None
    gen_desc: Optional[str] = None
    ecology: Optional[str] = None
    species: Optional[str] = None
    notes: Optional[str] = None
    refs: Optional[str] = None
    version: Optional[int] = None  # Added from MySQL schema
    num_views: int = Field(default=0)  # Added from MySQL schema, default 0
    last_view: Optional[datetime] = None  # Added from MySQL schema
    ok_for_export: bool = Field(default=True)  # Default from MySQL schema
    project_id: Optional[int] = None  # Added from MySQL schema


class ImageSchema(BaseModel):
    """Schema for image metadata."""

    image_id: int = Field(..., description="Unique identifier for the image")
    content_type: str = Field(..., description="MIME type of the image")
    copyright_holder: str = Field(..., description="Name of the copyright holder")
    license_id: int = Field(..., description="ID of the license")
    ok_for_export: Optional[bool] = Field(
        default=True, description="Whether image can be exported"
    )
    diagnostic: Optional[bool] = Field(
        default=False, description="Whether image is diagnostic"
    )
    width: Optional[int] = Field(default=None, description="Image width in pixels")
    height: Optional[int] = Field(default=None, description="Image height in pixels")
    rank: Optional[int] = Field(default=None, description="Display rank of the image")

    @field_validator("content_type")
    @classmethod
    def validate_content_type(cls, v):
        """Validate image content type."""
        allowed_types = ["image/jpeg", "image/png", "image/gif"]
        if v not in allowed_types:
            raise ValueError(f"Invalid content type. Must be one of: {allowed_types}")
        return v

    @field_validator("width", "height")
    @classmethod
    def validate_dimensions(cls, v):
        """Validate image dimensions."""
        if v is not None and v <= 0:
            raise ValueError("Image dimensions must be positive")
        return v

    @classmethod
    def from_csv_record(cls, record: Dict[str, Any]) -> "ImageSchema":
        """Create ImageSchema instance from CSV record with field mapping."""
        # Map CSV fields to schema fields
        mapped_record = {
            "image_id": record.get("id"),
            "content_type": record.get("content_type"),
            "copyright_holder": record.get("copyright_holder"),
            "license_id": int(record["license_id"]) if "license_id" in record else None,
            "ok_for_export": bool(int(record["ok_for_export"]))
            if "ok_for_export" in record
            else True,
            "diagnostic": bool(int(record["diagnostic"]))
            if "diagnostic" in record
            else False,
            "width": int(record["width"])
            if "width" in record and record["width"]
            else None,
            "height": int(record["height"])
            if "height" in record and record["height"]
            else None,
            "rank": int(record["rank"])
            if "rank" in record and record["rank"]
            else None,
        }

        # Handle license field mapping to license_id
        if "license" in record and not mapped_record["license_id"]:
            # Map license strings to IDs
            license_mapping = {
                "Creative Commons Wikipedia Compatible v3.0": 1,
                "CC BY-SA": 2,
                "CC BY": 3,
                "Public Domain": 4,
            }
            license_str = record["license"]
            mapped_record["license_id"] = license_mapping.get(
                license_str, 1
            )  # Default to 1 if unknown

        return cls(**mapped_record)


class ImagesObservationSchema(BaseModel):
    """Schema for the 'observation_images' table (Corrected table name)."""

    image_id: int
    observation_id: int
    rank: int = Field(default=0)  # Default from MySQL schema


class VoteSchema(BaseSchema):
    """Schema for the 'votes' table."""

    naming_id: Optional[int] = None
    user_id: Optional[int] = None
    observation_id: int = Field(default=0)  # Default from MySQL schema
    value: Optional[float] = None
    favorite: Optional[bool] = None


class NamingSchema(BaseSchema):
    """Schema for the 'namings' table."""

    observation_id: int
    name_id: int
    user_id: Optional[int] = None
    vote_cache: Optional[float] = Field(default=0.0)  # Default from MySQL schema
    reasons: Optional[str] = None


class NameClassificationSchema(BaseModel):
    """Schema for the 'name_classifications' table."""

    id: Optional[int] = None
    name_id: int
    domain: str = Field(..., min_length=1, description="Domain must not be empty.")
    kingdom: str = Field(..., min_length=1, description="Kingdom must not be empty.")
    phylum: str = Field(..., min_length=1, description="Phylum must not be empty.")
    class_name: str = Field(
        ..., min_length=1, alias="class", description="Class must not be empty."
    )
    order: str = Field(..., min_length=1, description="Order must not be empty.")
    family: str = Field(..., min_length=1, description="Family must not be empty.")


class HerbariumRecordSchema(BaseSchema):
    """Schema for the 'herbarium_records' table."""

    herbarium_id: int = Field(
        ..., description="Herbarium ID is required."
    )  # NOT Optional from MySQL
    user_id: int = Field(
        ..., description="User ID is required."
    )  # NOT Optional from MySQL
    initial_det: str = Field(
        ..., description="Initial Det is required."
    )  # NOT Optional and changed to str
    accession_number: str = Field(
        ..., description="Accession Number is required."
    )  # NOT Optional and changed to str
    notes: Optional[str] = None


class ObservationHerbariumRecordSchema(BaseModel):
    """Schema for the 'observation_herbarium_records' table."""

    observation_id: int
    herbarium_record_id: int


class ImageDataSchema(BaseModel):
    """Schema for image data within a species document."""

    image_id: Optional[int] = None
    url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    copyright_holder: Optional[str] = None
    license: Optional[str] = None
    content_type: str = "image/jpeg"
    quality_rating: int = 0
    observation_id: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None


class LocationSummarySchema(BaseModel):
    """Schema for location summary within a species document."""

    name: str
    count: int


class ObservationSummarySchema(BaseModel):
    """Schema for observation summary within a species document."""

    observation_id: Optional[int] = None
    when: Optional[date] = None
    vote_cache: float = 0
    location: Optional[Dict[str, Any]] = None


class DescriptionSchema(BaseModel):
    """Schema for consolidated descriptions within a species document."""

    general: Optional[str] = None
    diagnostic: Optional[str] = None
    distribution: Optional[str] = None
    habitat: Optional[str] = None
    look_alikes: Optional[str] = None
    uses: Optional[str] = None
    notes: Optional[str] = None
    references: Optional[List[str]] = Field(
        default_factory=list
    )  # Changed to List[str]


class SpeciesSchema(BaseModel):
    """Schema for consolidated species documents."""

    scientific_name: str = Field(..., description="Scientific Name")
    author: Optional[str] = None
    display_name: str = Field(..., description="Display Name")
    search_terms: List[str] = Field(default_factory=list, description="Search Terms")
    rank: int = Field(..., ge=1, le=100, description="Rank must be between 1 and 100")
    classification: Optional[Dict[str, str]] = None
    description: Optional[DescriptionSchema] = None
    images: Optional[List[ImageDataSchema]] = Field(
        default_factory=list
    )  # Changed to List[ImageDataSchema]
    observations: Optional[List[ObservationSummarySchema]] = Field(
        default_factory=list
    )  # Changed to List[ObservationSummarySchema]
    synonyms: Optional[List[NameSchema]] = Field(
        default_factory=list
    )  # Added synonyms field


class SynonymSchema(BaseModel):  # Define SynonymSchema
    """Schema for synonyms within a species document."""

    synonym_name: str
    synonym_author: Optional[str] = None
    synonym_deprecated: Optional[bool] = False


# Dictionary of schemas
SCHEMAS: Dict[str, Any] = {
    "observations": ObservationSchema,
    "names": NameSchema,
    "name_descriptions": NameDescriptionSchema,
    "locations": LocationSchema,
    "location_descriptions": LocationDescriptionSchema,
    "images": ImageSchema,
    "images_observations": ImagesObservationSchema,
    "votes": VoteSchema,
    "namings": NamingSchema,
    "name_classifications": NameClassificationSchema,
    "herbarium_records": HerbariumRecordSchema,
    "observation_herbarium_records": ObservationHerbariumRecordSchema,
    "species": SpeciesSchema,  # Add the new species schema
}
