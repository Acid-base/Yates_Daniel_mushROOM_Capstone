"""Schema definitions for data processing."""

from typing import Dict, Final, Any

# Schema definitions based on Mushroom Observer database structure
SCHEMAS: Final[Dict[str, Dict[str, type]]] = {
    "observations": {
        "id": int,
        "created_at": str,
        "updated_at": str,
        "when": str,
        "user_id": int,
        "specimen": bool,
        "notes": str,
        "thumb_image_id": int,
        "name_id": int,
        "location_id": int,
        "is_collection_location": bool,
        "vote_cache": float,
        "lat": float,
        "lng": float,
        "alt": int,
        "gps_hidden": bool,
        "needs_naming": bool,
        "location_lat": float,
        "location_lng": float
    },
    "names": {
        "id": int,
        "created_at": str,
        "updated_at": str,
        "text_name": str,
        "search_name": str,
        "display_name": str,
        "sort_name": str,
        "author": str,
        "citation": str,
        "deprecated": bool,
        "synonym_id": int,
        "correct_spelling_id": int,
        "rank": int,
        "notes": str,
        "classification": str,
        "ok_for_export": bool,
        "lifeform": str,
        "locked": bool
    },
    "name_descriptions": {
        "id": int,
        "created_at": str,
        "updated_at": str,
        "user_id": int,
        "name_id": int,
        "review_status": int,
        "source_type": int,
        "source_name": str,
        "public": bool,
        "locale": str,
        "license_id": int,
        "gen_desc": str,
        "diag_desc": str,
        "distribution": str,
        "habitat": str,
        "look_alikes": str,
        "uses": str,
        "notes": str,
        "refs": str,
        "classification": str
    },
    "locations": {
        "id": int,
        "created_at": str,
        "updated_at": str,
        "user_id": int,
        "name": str,
        "north": float,
        "south": float,
        "west": float,
        "east": float,
        "high": float,
        "low": float,
        "notes": str,
        "scientific_name": str,
        "locked": bool,
        "hidden": bool
    },
    "location_descriptions": {
        "id": int,
        "created_at": str,
        "updated_at": str,
        "user_id": int,
        "location_id": int,
        "source_type": int,
        "source_name": str,
        "public": bool,
        "locale": str,
        "license_id": int,
        "gen_desc": str,
        "ecology": str,
        "species": str,
        "notes": str,
        "refs": str
    },
    "images": {
        "id": int,
        "created_at": str,
        "updated_at": str,
        "content_type": str,
        "user_id": int,
        "when": str,
        "notes": str,
        "copyright_holder": str,
        "license_id": int,
        "ok_for_export": bool,
        "vote_cache": float,
        "width": int,
        "height": int,
        "gps_stripped": bool,
        "transferred": bool,
        "diagnostic": bool
    },
    "images_observations": {
        "image_id": int,
        "observation_id": int,
        "rank": int
    },
    "votes": {
        "id": int,
        "created_at": str,
        "updated_at": str,
        "naming_id": int,
        "user_id": int,
        "observation_id": int,
        "value": float,
        "favorite": bool
    },
    "namings": {
        "id": int,
        "created_at": str,
        "updated_at": str,
        "observation_id": int,
        "name_id": int,
        "user_id": int,
        "vote_cache": float,
        "reasons": str
    },
    "name_classifications": {
        "id": int,
        "name_id": int,
        "domain": str,
        "kingdom": str,
        "phylum": str,
        "class": str,
        "order": str,
        "family": str
    },
    "herbarium_records": {
        "id": int,
        "herbarium_id": int,
        "user_id": int,
        "initial_det": str,
        "accession_number": str,
        "notes": str,
        "created_at": str,
        "updated_at": str
    },
    "observation_herbarium_records": {
        "observation_id": int,
        "herbarium_record_id": int
    }
} 