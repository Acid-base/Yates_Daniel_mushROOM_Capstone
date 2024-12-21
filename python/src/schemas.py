from typing import Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel, validator, Field, constr, confloat
from enum import Enum


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
    created_at: datetime
    updated_at: datetime

    @validator("created_at", "updated_at", pre=True)
    def parse_datetime(cls, value):
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                raise ValueError(
                    f"Invalid datetime format: {value}. Expected ISO format (YYYY-MM-DDTHH:MM:SSZ or YYYY-MM-DDTHH:MM:SS+HH:MM)."
                )
        return value


class ObservationBase(BaseModel):
    """Base model for observations."""

    id: int = Field(..., gt=0, description="Observation ID must be greater than 0.")
    name_id: int = Field(..., gt=0, description="Name ID must be greater than 0.")
    when: datetime
    location_id: Optional[int] = Field(None, gt=0, description="Location ID must be greater than 0 if provided.")
    lat: Optional[confloat(ge=-90, le=90)] = Field(None, description="Latitude must be between -90 and 90.")
    lng: Optional[confloat(ge=-180, le=180)] = Field(None, description="Longitude must be between -180 and 180.")
    alt: Optional[float] = None
    vote_cache: Optional[float] = None
    is_collection_location: bool = False

    @validator("when")
    def validate_when(cls, v):
        if v > datetime.now():
            raise ValueError("Observation date cannot be in the future.")
        return v


class ObservationSchema(BaseSchema):
    """Schema for the 'observations' table."""

    when: datetime
    user_id: int
    specimen: bool
    notes: Optional[str] = None
    thumb_image_id: Optional[int] = None
    name_id: Optional[int] = None
    location_id: Optional[int] = None
    is_collection_location: bool
    vote_cache: Optional[float] = None
    lat: Optional[confloat(ge=-90, le=90)] = None
    lng: Optional[confloat(ge=-180, le=180)] = None
    alt: Optional[int] = None
    gps_hidden: bool
    needs_naming: bool
    location_lat: Optional[confloat(ge=-90, le=90)] = None
    location_lng: Optional[confloat(ge=-180, le=180)] = None

    @validator("when", pre=True)
    def parse_when_datetime(cls, value):
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                raise ValueError(
                    f"Invalid datetime format: {value}. Expected ISO format (YYYY-MM-DDTHH:MM:SSZ or YYYY-MM-DDTHH:MM:SS+HH:MM)."
                )
        return value


class NameSchema(BaseSchema):
    """Schema for the 'names' table."""

    text_name: constr(min_length=1, description="Text name must not be empty.")
    search_name: constr(min_length=1, description="Search name must not be empty.")
    display_name: constr(min_length=1, description="Display name must not be empty.")
    sort_name: constr(min_length=1, description="Sort name must not be empty.")
    author: Optional[str] = None
    citation: Optional[str] = None
    deprecated: bool
    synonym_id: Optional[int] = None
    correct_spelling_id: Optional[int] = None
    rank: int
    notes: Optional[str] = None
    classification: Optional[str] = None
    ok_for_export: bool
    lifeform: Optional[str] = None
    locked: bool


class NameDescriptionSchema(BaseSchema):
    """Schema for the 'name_descriptions' table."""

    user_id: int
    name_id: int
    review_status: ReviewStatus
    source_type: SourceType
    source_name: Optional[str] = None
    public: bool
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


class LocationSchema(BaseSchema):
    """Schema for the 'locations' table."""

    user_id: int
    name: constr(min_length=1, description="Location name must not be empty.")
    north: float
    south: float
    west: float
    east: float
    high: Optional[float] = None
    low: Optional[float] = None
    notes: Optional[str] = None
    scientific_name: Optional[str] = None
    locked: bool
    hidden: bool


class LocationDescriptionSchema(BaseSchema):
    """Schema for the 'location_descriptions' table."""

    user_id: int
    location_id: int
    source_type: SourceType
    source_name: Optional[str] = None
    public: bool
    locale: Optional[str] = None
    license_id: Optional[int] = None
    gen_desc: Optional[str] = None
    ecology: Optional[str] = None
    species: Optional[str] = None
    notes: Optional[str] = None
    refs: Optional[str] = None


class ImageSchema(BaseSchema):
    """Schema for the 'images' table."""

    content_type: constr(min_length=1, description="Content type must not be empty.")
    user_id: int
    when: datetime
    notes: Optional[str] = None
    copyright_holder: Optional[str] = None
    license_id: int
    ok_for_export: bool
    vote_cache: Optional[float] = None
    width: int
    height: int
    gps_stripped: bool
    transferred: bool
    diagnostic: bool

    @validator("when", pre=True)
    def parse_when_datetime(cls, value):
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                raise ValueError(
                    f"Invalid datetime format: {value}. Expected ISO format (YYYY-MM-DDTHH:MM:SSZ or YYYY-MM-DDTHH:MM:SS+HH:MM)."
                )
        return value


class ImagesObservationSchema(BaseModel):
    """Schema for the 'images_observations' table."""

    image_id: int
    observation_id: int
    rank: int


class VoteSchema(BaseSchema):
    """Schema for the 'votes' table."""

    naming_id: int
    user_id: int
    observation_id: int
    value: float
    favorite: bool


class NamingSchema(BaseSchema):
    """Schema for the 'namings' table."""

    observation_id: int
    name_id: int
    user_id: int
    vote_cache: Optional[float] = None
    reasons: Optional[str] = None


class NameClassificationSchema(BaseModel):
    """Schema for the 'name_classifications' table."""

    id: int
    name_id: int
    domain: constr(min_length=1, description="Domain must not be empty.")
    kingdom: constr(min_length=1, description="Kingdom must not be empty.")
    phylum: constr(min_length=1, description="Phylum must not be empty.")
    class_name: constr(min_length=1, alias="class", description="Class must not be empty.")
    order: constr(min_length=1, description="Order must not be empty.")
    family: constr(min_length=1, description="Family must not be empty.")


class HerbariumRecordSchema(BaseSchema):
    """Schema for the 'herbarium_records' table."""

    herbarium_id: int
    user_id: int
    initial_det: Optional[str] = None
    accession_number: Optional[str] = None
    notes: Optional[str] = None


class ObservationHerbariumRecordSchema(BaseModel):
    """Schema for the 'observation_herbarium_records' table."""

    observation_id: int
    herbarium_record_id: int


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
}
