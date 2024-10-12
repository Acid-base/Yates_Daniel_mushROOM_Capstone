import csv
import logging
from collections import defaultdict
from datetime import datetime
from functools import partial
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from pymongo import MongoClient, UpdateOne

# Type Aliases
Schema = Dict[str, type]
DataDict = Dict[str, List[Dict[str, Any]]]

# --- Constants ---
MONGODB_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "my_database"

# --- Data Loading ---
def load_csv_data(filename: str, delimiter: str = "\t", schema: Optional[Dict[str, type]] = None) -> List[Dict[str, Any]]:
    """Loads data from a CSV file into a list of dictionaries, applying schema validation."""
    try:
        with open(filename, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile, delimiter=delimiter)

            if schema:
                missing_fields = set(schema.keys()) - set(reader.fieldnames)
                if missing_fields:
                    logging.warning(f"Fields {missing_fields} not found in the headers of file {filename}")

            data = []
            for row_num, row in enumerate(reader, start=2):  # Start from 2 to account for header row
                if schema:
                    for field, field_type in schema.items():
                        if field in row:
                            original_value = row[field]
                            try:
                                row[field] = safe_cast(original_value, field_type)
                                if row[field] != original_value:
                                    logging.debug(f"File: {filename}, Row: {row_num}, Field: {field}, "
                                                  f"Original: '{original_value}', Converted: '{row[field]}', "
                                                  f"Type: {type(row[field])}, Expected type: {field_type.__name__}")
                            except Exception as e:
                                logging.error(f"Error in file {filename}, row {row_num}, field {field}: {str(e)}")
                                logging.error(f"Original value: '{original_value}', Expected type: {field_type.__name__}")
                data.append(row)
            return data
    except FileNotFoundError:
        logging.error(f"File not found: {filename}")
        return []

# --- Data Processing Functions ---
def process_names(names: List[Dict[str, Any]], species_dict: Dict[int, Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
    """Processes names data and updates the species dictionary."""
    for name in names:
        name_id = name["id"]
        if name_id is not None:
            species_dict[name_id].update({
                "id": name_id,
                "text_name": name["text_name"],
                "author": name["author"],
                "deprecated": name["deprecated"],
                "correct_spelling_id": name["correct_spelling_id"],
                "rank": name["rank"],
            })
    return species_dict

def process_taxonomy(taxonomy: List[Dict[str, Any]], species_dict: Dict[int, Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
    """Processes taxonomy data and updates the species dictionary."""
    for taxon in taxonomy:
        name_id = taxon["name_id"]
        if name_id is not None:
            species_dict[name_id]["taxonomy"] = {
                "kingdom": taxon["kingdom"],
                "phylum": taxon["phylum"],
                "class": taxon["class"],
                "order": taxon["order"],
                "family": taxon["family"],
            }
    return species_dict

def process_name_descriptions(name_descriptions: List[Dict[str, Any]], species_dict: Dict[int, Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
    """Processes name descriptions data and updates the species dictionary."""
    name_descriptions_by_name_id = defaultdict(list)
    for desc in name_descriptions:
        name_descriptions_by_name_id[desc["name_id"]].append(desc)

    for name_id, descriptions in name_descriptions_by_name_id.items():
        latest_desc = max(descriptions, key=lambda x: x.get("version") or 0, default={})
        species_dict[name_id]["description"] = {
            "gen_desc": latest_desc.get("general_description"),
            "diag_desc": latest_desc.get("diagnostic_description"),
            "distribution": latest_desc.get("distribution"),
            "habitat": latest_desc.get("habitat"),
            "look_alikes": latest_desc.get("look_alikes"),
            "uses": latest_desc.get("uses"),
            "refs": latest_desc.get("refs"),
        }
    return species_dict

def process_observations(observations: List[Dict[str, Any]], images_observations: List[Dict[str, Any]], species_dict: Dict[int, Dict[str, Any]]) -> Tuple[Dict[int, Dict[str, Any]], Dict[int, Set[int]]]:
    """Processes observations and images_observations data, updating the species dictionary and returning image mappings."""
    observations_by_name_id = defaultdict(list)
    images_by_observation = defaultdict(set)

    for observation in observations:
        name_id = observation["name_id"]
        obs_id = observation["id"]
        try:
            obs_date = datetime.strptime(observation["when"], "%Y-%m-%d").date()
        except (ValueError, TypeError) as e:
            logging.warning(f"Invalid date format for observation {obs_id}: {e}")
            obs_date = None

        if name_id is not None and obs_id is not None:
            observations_by_name_id[name_id].append({
                "id": obs_id,
                "when": obs_date,
                "location_id": observation["location_id"],
                "lat": observation["lat"],
                "lng": observation["lng"],
                "image_ids": set(),
            })

    for image_obs in images_observations:
        image_id = image_obs["image_id"]
        obs_id = image_obs["observation_id"]
        if image_id is not None and obs_id is not None:
            images_by_observation[obs_id].add(image_id)

    for name_id, observations in observations_by_name_id.items():
        for obs in observations:
            obs["image_ids"].update(images_by_observation.get(obs["id"], set()))

    for name_id, observations in observations_by_name_id.items():
        species_dict[name_id]["observations"] = observations

    return species_dict, images_by_observation

def process_images(images: List[Dict[str, Any]], images_by_observation: Dict[int, Set[int]], species_dict: Dict[int, Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
    """Processes images data and updates the species dictionary."""
    image_summaries = {}
    for image in images:
        image_id = image["id"]
        if image_id is not None:
            license_name = image.get("license", "Unknown License")
            image_summaries[image_id] = {
                "id": image_id,
                "copyright_holder": image["copyright_holder"],
                "license": license_name,
            }

    for name_id, species_data in species_dict.items():
        species_data["images"] = [
            image_summaries[img_id]
            for obs in species_data.get("observations", [])
            for img_id in obs["image_ids"]
            if img_id in image_summaries
        ]

    return species_dict

def process_locations(locations: List[Dict[str, Any]], location_descriptions_by_id: Dict[int, Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
    """Processes locations data and updates the locations dictionary."""
    locations_dict = {}
    for location in locations:
        location_id = location["id"]
        if location_id is not None:
            loc_desc = location_descriptions_by_id.get(location_id, {})
            locations_dict[location_id] = {
                "id": location_id,
                "name": location["name"],
                "lat": location["north"],
                "lng": location["west"],
                "description": {
                    "gen_desc": loc_desc.get("general_description"),
                    "ecology": loc_desc.get("ecology"),
                },
            }
    return locations_dict

def deduplicate_species(species_dict: Dict[int, Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
    """Deduplicates species data by removing duplicate locations and images."""
    for species in species_dict.values():
        species["locations"] = list({obs["location_id"] for obs in species.get("observations", []) if obs["location_id"] is not None})
        species["images"] = list({tuple(sorted(d.items())) for d in species.get("images", [])})
    return species_dict

def process_data(data: DataDict) -> Tuple[Dict[int, Dict[str, Any]], Dict[int, Dict[str, Any]]]:
    """Processes and aggregates data from the loaded CSV files."""
    species_dict = defaultdict(dict)
    location_descriptions_by_id = {loc["location_id"]: loc for loc in data["location_descriptions"]}

    species_dict = process_names(data["names"], species_dict)
    species_dict = process_taxonomy(data["taxonomy"], species_dict)
    species_dict = process_name_descriptions(data["name_descriptions"], species_dict)
    species_dict, images_by_observation = process_observations(data["observations"], data["images_observations"], species_dict)
    species_dict = process_images(data["images"], images_by_observation, species_dict)
    locations_dict = process_locations(data["locations"], location_descriptions_by_id)

    species_dict = deduplicate_species(species_dict)

    return species_dict, locations_dict

# --- MongoDB Insertion ---
def insert_to_mongodb(collection_name: str, data: List[Dict[str, Any]], batch_size: int = 1000) -> None:
    """Inserts data into a MongoDB collection using bulk updates."""
    client = MongoClient(MONGODB_URI)
    db = client[DATABASE_NAME]
    collection = db[collection_name]

    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]
        operations = [UpdateOne({"_id": item["id"]}, {"$set": item}, upsert=True) for item in batch]
        try:
            result = collection.bulk_write(operations)
            total_processed = result.upserted_count + result.modified_count
            logging.info(f"Processed {total_processed} items in {collection_name}.")
        except Exception as e:
            logging.exception(f"Error inserting data into {collection_name}: {e}")

# --- Main Function ---
def main():
    """Loads data, processes it, and inserts it into MongoDB."""
    # Define data files and schema
    data_files = {
        "names": "names.csv",
        "name_descriptions": "name_descriptions.csv",
        "observations": "observations.csv",
        "locations": "locations.csv",
        "images": "images.csv",
        "taxonomy": "name_classifications.csv",
        "images_observations": "images_observations.csv",
        "location_descriptions": "location_descriptions.csv",
    }

    schema = {
        "names": {
            "id": int,
            "text_name": str,
            "author": str,
            "deprecated": bool,
            "correct_spelling_id": int,
            "rank": int,
        },
        "name_descriptions": {
            "name_id": int,
            "general_description": str,
            "diagnostic_description": str,
            "distribution": str,
            "habitat": str,
            "look_alikes": str,
            "uses": str,
            "refs": str,
            "license_id": int,
            "version": int,
        },
        "observations": {
            "id": int,
            "name_id": int,
            "when": str,
            "location_id": int,
            "lat": float,
            "lng": float,
        },
        "locations": {
            "id": int,
            "name": str,
            "north": float,
            "west": float,
        },
        "images": {
            "id": int,
            "observation_id": int,
            "copyright_holder": str,
            "license": str,
            "license_id": int,
        },
        "taxonomy": {
            "name_id": int,
            "kingdom": str,
            "phylum": str,
            "class": str,
            "order": str,
            "family": str,
        },
        "images_observations": {
            "image_id": int,
            "observation_id": int,
        },
        "location_descriptions": {
            "location_id": int,
            "general_description": str,
            "ecology": str,
        },
    }

    # Load data
    data = {key: load_csv_data(filename, schema=schema.get(key)) for key, filename in data_files.items()}

    # Process data
    species_dict, locations_dict = process_data(data)

    # Insert data into MongoDB
    insert_to_mongodb("species", list(species_dict.values()))
    insert_to_mongodb("locations", list(locations_dict.values()))

    logging.info("Data migration complete!")

# --- Helper Function ---
def safe_cast(val, to_type):
    """Safely casts a value to a given type."""
    try:
        return to_type(val)
    except (ValueError, TypeError):
        return val

if __name__ == "__main__":
    main()
