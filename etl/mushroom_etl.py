#!/usr/bin/env python3
"""
Mushroom Observer ETL Pipeline

This script extracts data from Mushroom Observer CSV files, transforms it according to
field guide requirements, and loads it into MongoDB.
"""

import logging
import os
import re
import warnings
from datetime import datetime

import numpy as np
import pandas as pd
import pymongo
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from tqdm import tqdm

# Suppress pandas warnings
warnings.filterwarnings("ignore")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("mushroom_etl.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# MongoDB connection settings
MONGODB_CONNECTION_STRING = os.getenv("MONGODB_CONNECTION_STRING")
MONGODB_DB_NAME = os.getenv("DB_NAME", "mushroom_field_guide")
MONGODB_COLLECTION = os.getenv("COLLECTION_NAME", "species")

# Data directory
DATA_DIR = os.getenv("DATA_DIR", "data")
BASE_URL = "https://mushroomobserver.org/"


# File paths
def get_file_path(filename):
    return os.path.join(DATA_DIR, filename)


# License mapping function
def map_license_url(license_text):
    """Map license text to a standardized URL."""
    license_map = {
        "Creative Commons Attribution-ShareAlike": "https://creativecommons.org/licenses/by-sa/4.0/",
        "Creative Commons Attribution": "https://creativecommons.org/licenses/by/4.0/",
        "Creative Commons Attribution-NonCommercial-ShareAlike": "https://creativecommons.org/licenses/by-nc-sa/4.0/",
        "Creative Commons Attribution-NonCommercial": "https://creativecommons.org/licenses/by-nc/4.0/",
        "Creative Commons Wikipedia Compatible": "https://creativecommons.org/licenses/by-sa/3.0/",
        "Public Domain": "https://creativecommons.org/publicdomain/zero/1.0/",
    }

    # Look for partial matches
    for key in license_map:
        if key in license_text:
            return license_map[key]

    # Default
    return "https://creativecommons.org/licenses/"


#
# EXTRACTION FUNCTIONS
#
def load_csv_files():
    """Load all CSV files with appropriate settings for each."""
    logger.info("Loading CSV files from %s", DATA_DIR)

    try:
        names_df = pd.read_csv(get_file_path("names.csv"), sep="\t", na_values=["NULL"])
        logger.info(f"Loaded names.csv: {len(names_df)} rows")

        name_descriptions_df = pd.read_csv(
            get_file_path("name_descriptions.csv"),
            sep="\t",
            na_values=["NULL"],
            quoting=3,  # QUOTE_NONE
            engine="python",  # For handling complex quoting
        )
        logger.info(f"Loaded name_descriptions.csv: {len(name_descriptions_df)} rows")

        name_classifications_df = pd.read_csv(
            get_file_path("name_classifications.csv"), sep="\t"
        )
        logger.info(
            f"Loaded name_classifications.csv: {len(name_classifications_df)} rows"
        )

        observations_df = pd.read_csv(
            get_file_path("observations.csv"), sep="\t", na_values=["NULL"]
        )
        logger.info(f"Loaded observations.csv: {len(observations_df)} rows")

        images_df = pd.read_csv(
            get_file_path("images.csv"), sep="\t", na_values=["NULL"]
        )
        logger.info(f"Loaded images.csv: {len(images_df)} rows")

        images_observations_df = pd.read_csv(
            get_file_path("images_observations.csv"), sep="\t", na_values=["NULL"]
        )
        logger.info(
            f"Loaded images_observations.csv: {len(images_observations_df)} rows"
        )

        locations_df = pd.read_csv(
            get_file_path("locations.csv"), sep="\t", na_values=["NULL"]
        )
        logger.info(f"Loaded locations.csv: {len(locations_df)} rows")

        location_descriptions_df = pd.read_csv(
            get_file_path("location_descriptions.csv"),
            sep="\t",
            na_values=["NULL"],
            quoting=3,  # QUOTE_NONE
            engine="python",
        )
        logger.info(
            f"Loaded location_descriptions.csv: {len(location_descriptions_df)} rows"
        )

        return {
            "names": names_df,
            "name_descriptions": name_descriptions_df,
            "name_classifications": name_classifications_df,
            "observations": observations_df,
            "images": images_df,
            "images_observations": images_observations_df,
            "locations": locations_df,
            "location_descriptions": location_descriptions_df,
        }

    except Exception as e:
        logger.error(f"Error loading CSV files: {str(e)}")
        raise


#
# TRANSFORMATION FUNCTIONS
#
def clean_description(text):
    """Clean HTML, Textile markup, extract URLs, normalize text."""
    if pd.isna(text) or not isinstance(text, str):
        return None, []

    # Extract URLs - using patterns found in sample data
    urls = []

    # Extract HTML links: <a href="http://url">text</a>
    html_links = re.findall(r'<a href="(https?://[^"]+)">[^<]+</a>', text)
    urls.extend(html_links)

    # Extract Textile links: "text":http://url
    textile_links = re.findall(r'"[^"]+"\s*:\s*(https?://\S+)', text)
    urls.extend(textile_links)

    # Extract bare URLs
    bare_urls = re.findall(r'(?<![">:])(https?://\S+)(?!["\'])', text)
    urls.extend(bare_urls)

    # Use BeautifulSoup to handle HTML tags
    try:
        soup = BeautifulSoup(text, "html.parser")
        text = soup.get_text()
    except:
        # Fallback to regex if BeautifulSoup fails
        text = re.sub(r"<[^>]+>", "", text)

    # Remove Textile links but keep the link text
    text = re.sub(r'"([^"]+)"\s*:https?://\S+', r"\1", text)

    # Normalize newlines
    text = text.replace("\\n", "\n")

    # Convert underscored scientific names to regular text
    text = re.sub(r"_([^_]+)_", r"\1", text)

    # Remove excessive whitespace
    text = re.sub(r"\s+", " ", text).strip()

    # Validate content (reject if just an address or URL)
    if re.match(
        r"^\d+\s+[A-Za-z\s]+,\s+[A-Za-z\s]+,\s+[A-Z]{2}\s+\d+", text
    ) or text.startswith("http"):
        return None, urls

    # If text is too short after cleaning, it's probably not useful
    if len(text) < 5:
        return None, urls

    return text, list(set(urls))


def extract_field_data(row):
    """Extract clean description fields and references from a row."""
    refs = []
    fields = {}

    # Process each description field
    for field in [
        "general_description",
        "diagnostic_description",
        "habitat",
        "distribution",
        "uses",
        "look_alikes",
        "notes",
    ]:
        if field in row and not pd.isna(row[field]):
            clean_text, urls = clean_description(row[field])
            if clean_text:
                fields[field.replace("_description", "")] = clean_text
            refs.extend(urls)

    # Extract common name with the exact format seen in samples
    if "notes" in row and not pd.isna(row["notes"]):
        # Exact pattern found in sample: "Common Name: Plums and Custard"
        common_name_match = re.search(r'"Common Name:\s+([^"]+)"', row["notes"])
        if common_name_match:
            fields["common_name"] = common_name_match.group(1).strip()

    return fields, list(set(refs))


def extract_regions(location_names):
    """Extract countries, states, regions from location names."""
    countries = set()
    states = set()
    regions = set()

    for loc in location_names:
        if pd.isna(loc):
            continue

        parts = loc.split(", ")
        if len(parts) >= 2:
            # Last part is usually country
            country = parts[-1]
            countries.add(country)

            # Second to last is usually state or province
            if len(parts) >= 3:
                state = parts[-2]
                states.add(state)

                # Third to last might be county/region
                if len(parts) >= 4:
                    region = parts[-3]
                    regions.add(region)

    return list(countries), list(states), list(regions)


def transform_data(dataframes):
    """Transform extracted dataframes into species documents."""
    logger.info("Starting data transformation")

    # Filter for species rank only and not deprecated
    species_df = dataframes["names"][
        (dataframes["names"]["rank"] == 4) & (dataframes["names"]["deprecated"] == 0)
    ]
    logger.info(f"Filtered {len(species_df)} species records")

    # Convert id columns to consistent type (int64) for all dataframes before merging
    for df_name in [
        "names",
        "name_descriptions",
        "name_classifications",
        "observations",
        "locations",
    ]:
        if df_name in dataframes:
            if "id" in dataframes[df_name].columns:
                dataframes[df_name]["id"] = pd.to_numeric(
                    dataframes[df_name]["id"], errors="coerce"
                )
            if "name_id" in dataframes[df_name].columns:
                dataframes[df_name]["name_id"] = pd.to_numeric(
                    dataframes[df_name]["name_id"], errors="coerce"
                )
            if "location_id" in dataframes[df_name].columns:
                dataframes[df_name]["location_id"] = pd.to_numeric(
                    dataframes[df_name]["location_id"], errors="coerce"
                )

    # Force consistent types for images_observations joins
    dataframes["images_observations"]["image_id"] = pd.to_numeric(
        dataframes["images_observations"]["image_id"], errors="coerce"
    )
    dataframes["images_observations"]["observation_id"] = pd.to_numeric(
        dataframes["images_observations"]["observation_id"], errors="coerce"
    )
    dataframes["images"]["id"] = pd.to_numeric(
        dataframes["images"]["id"], errors="coerce"
    )

    # Join with classifications
    species_with_class = pd.merge(
        species_df,
        dataframes["name_classifications"],
        left_on="id",
        right_on="name_id",
        how="left",
    )

    # Log columns to identify correct names after merge
    logger.info(f"Columns in species_with_class: {species_with_class.columns.tolist()}")

    # Determine id column name for species_with_class
    class_id_col = "id_x" if "id_x" in species_with_class.columns else "id"
    logger.info(f"Using '{class_id_col}' as classification ID column")

    # Join with descriptions
    species_descriptions = pd.merge(
        species_with_class,
        dataframes["name_descriptions"],
        left_on="id",
        right_on="name_id",
        how="left",
    )

    # Log columns to identify correct names after merge
    logger.info(
        f"Columns in species_descriptions: {species_descriptions.columns.tolist()}"
    )

    # Determine id column name
    species_id_col = "id_x" if "id_x" in species_descriptions.columns else "id"
    logger.info(f"Using '{species_id_col}' as species ID column")

    # Find observations for each species
    species_observations = pd.merge(
        species_df[["id"]],
        dataframes["observations"],
        left_on="id",
        right_on="name_id",
        how="left",
    )

    # Check if vote_cache exists in observations
    obs_columns = species_observations.columns.tolist()
    logger.info(f"Observation columns: {obs_columns}")
    has_vote_cache = "vote_cache" in obs_columns

    # Join observations with locations
    observations_with_locations = pd.merge(
        species_observations,
        dataframes["locations"],
        left_on="location_id",
        right_on="id",
        how="inner",
    )

    # Log columns to identify the correct location name column
    logger.info(
        f"Columns in observations_with_locations: {observations_with_locations.columns.tolist()}"
    )

    # Check for the location name column - according to the data report, it should be 'name' in locations.csv
    location_name_col = "name"
    if location_name_col not in observations_with_locations.columns:
        # Try common suffixes from merges
        for suffix in ["", "_x", "_y"]:
            if f"name{suffix}" in observations_with_locations.columns:
                location_name_col = f"name{suffix}"
                break

    logger.info(f"Using '{location_name_col}' as location name column")

    # Aggregate location data by species with the correct column name
    location_data = (
        observations_with_locations.groupby("name_id")
        .agg(
            location_names=(location_name_col, lambda x: list(set(x))),
            north=("north", "max"),
            south=("south", "min"),
            east=("east", "max"),
            west=("west", "min"),
            high=(
                "high",
                lambda x: np.nanmax(x) if not np.isnan(np.nanmax(x)) else None,
            ),
            low=("low", lambda x: np.nanmin(x) if not np.isnan(np.nanmin(x)) else None),
        )
        .reset_index()
    )

    # Join observations with images
    images_observations = pd.merge(
        dataframes["images_observations"],
        species_observations,
        left_on="observation_id",
        right_on="id_y",
        how="inner",
    )

    # Now join with image data
    images_with_data = pd.merge(
        images_observations,
        dataframes["images"],
        left_on="image_id",
        right_on="id",
        how="inner",
    )

    # Log available columns
    logger.info(
        f"Available columns in images_with_data: {images_with_data.columns.tolist()}"
    )

    # Select best image per species - either by vote_cache or by choosing first
    if "vote_cache_x" in images_with_data.columns:
        sort_col = "vote_cache_x"
    elif "vote_cache_y" in images_with_data.columns:
        sort_col = "vote_cache_y"
    elif "vote_cache" in images_with_data.columns:
        sort_col = "vote_cache"
    else:
        # No vote_cache column, use image quality as fallback or just take first image
        sort_col = "quality" if "quality" in images_with_data.columns else None

    # Select best image per species
    if sort_col:
        logger.info(f"Sorting images by {sort_col}")
        best_images = (
            images_with_data[images_with_data["ok_for_export"] == 1]
            .sort_values(sort_col, ascending=False)
            .groupby("name_id")
            .first()
            .reset_index()
        )
    else:
        logger.info(
            "No sorting criteria found - using first available image per species"
        )
        best_images = (
            images_with_data[images_with_data["ok_for_export"] == 1]
            .groupby("name_id")
            .first()
            .reset_index()
        )

    # Aggregate observation data by species
    observation_stats = (
        species_observations.groupby("name_id")
        .agg(
            count=("id_y", "count"),
            avg_vote=("vote_cache", "mean"),
            first_date=("when", "min"),
            last_date=("when", "max"),
        )
        .reset_index()
    )

    # Now create the species documents
    species_documents = []

    for idx, species_row in tqdm(
        species_df.iterrows(), total=len(species_df), desc="Processing species"
    ):
        species_id = species_row["id"]

        # Get species classification data
        class_data = species_with_class[species_with_class[class_id_col] == species_id]
        if not class_data.empty:
            class_data = class_data.iloc[0]
        else:
            class_data = {}

        # Get species description data
        desc_data = species_descriptions[
            species_descriptions[species_id_col] == species_id
        ]
        if not desc_data.empty:
            desc_data = desc_data.iloc[0]
            desc_fields, references = extract_field_data(desc_data)
        else:
            desc_data = {}
            desc_fields = {}
            references = []

        # Get image data
        image_data = best_images[best_images["name_id"] == species_id]
        image_info = None
        if not image_data.empty:
            image_row = image_data.iloc[0]
            image_info = {
                "url": f"https://mushroomobserver.org/images/640/{image_row['image_id']}.jpg",
                "copyright": f"© {image_row['copyright_holder']}",
                "license": image_row["license"],
                "license_url": map_license_url(image_row["license"]),
            }

        # Get location data
        loc_data = location_data[location_data["name_id"] == species_id]
        regional_info = None
        if not loc_data.empty:
            loc_row = loc_data.iloc[0]
            if "location_names" in loc_row and loc_row["location_names"]:
                countries, states, regions = extract_regions(loc_row["location_names"])
                regional_info = {
                    "countries": countries,
                    "states": states,
                    "regions": regions,
                }

        # Get observation stats
        obs_data = observation_stats[observation_stats["name_id"] == species_id]
        obs_info = None
        if not obs_data.empty:
            obs_row = obs_data.iloc[0]
            obs_info = {
                "count": int(obs_row["count"]),
                "confidence": float(obs_row["avg_vote"])
                if not pd.isna(obs_row["avg_vote"])
                else None,
                "first_observed": obs_row["first_date"]
                if not pd.isna(obs_row["first_date"])
                else None,
                "last_observed": obs_row["last_date"]
                if not pd.isna(obs_row["last_date"])
                else None,
            }

        # Create the document
        doc = {
            "scientific_name": species_row["text_name"],
            "authority": species_row["author"]
            if not pd.isna(species_row["author"])
            else None,
            "classification": {
                "kingdom": class_data.get("kingdom")
                if not pd.isna(class_data.get("kingdom", np.nan))
                else "Fungi",
                "phylum": class_data.get("phylum")
                if not pd.isna(class_data.get("phylum", np.nan))
                else None,
                "class_name": class_data.get("class")
                if not pd.isna(class_data.get("class", np.nan))
                else None,
                "order": class_data.get("order")
                if not pd.isna(class_data.get("order", np.nan))
                else None,
                "family": class_data.get("family")
                if not pd.isna(class_data.get("family", np.nan))
                else None,
            },
        }

        # Add common name if available
        if "common_name" in desc_fields:
            doc["common_name"] = desc_fields["common_name"]

        # Add description fields
        description = {}
        for key, value in desc_fields.items():
            if key != "common_name" and value:
                description[key] = value

        if description:
            doc["description"] = description

        # Add image if available
        if image_info:
            doc["image"] = image_info

        # Add regional distribution if available
        if regional_info:
            doc["regional_distribution"] = regional_info

        # Add observation data if available
        if obs_info:
            doc["observation_data"] = obs_info

        # Add references if available
        if references:
            doc["references"] = references

        # Add timestamp
        doc["last_updated"] = datetime.now().isoformat()

        species_documents.append(doc)

    logger.info(f"Created {len(species_documents)} species documents")
    return species_documents


#
# LOADING FUNCTIONS
#
def load_to_mongodb(documents):
    """Load transformed documents into MongoDB."""
    if not MONGODB_CONNECTION_STRING:
        logger.error("MongoDB connection string not found in environment variables")
        raise ValueError("MONGODB_CONNECTION_STRING environment variable is required")

    logger.info("Connecting to MongoDB")
    client = pymongo.MongoClient(MONGODB_CONNECTION_STRING)
    db = client[MONGODB_DB_NAME]
    collection = db[MONGODB_COLLECTION]

    # Drop existing collection if it exists
    if MONGODB_COLLECTION in db.list_collection_names():
        logger.info(f"Dropping existing collection: {MONGODB_COLLECTION}")
        db.drop_collection(MONGODB_COLLECTION)

    # Insert documents in batches
    batch_size = 1000
    total_batches = (len(documents) + batch_size - 1) // batch_size

    logger.info(f"Inserting {len(documents)} documents in {total_batches} batches")

    for i in tqdm(range(0, len(documents), batch_size), desc="Loading to MongoDB"):
        batch = documents[i : i + batch_size]
        try:
            collection.insert_many(batch)
        except Exception as e:
            logger.error(f"Error inserting batch {i // batch_size + 1}: {str(e)}")
            continue

    # Create indexes for efficient querying
    logger.info("Creating indexes")
    collection.create_index("scientific_name")
    collection.create_index("common_name")
    collection.create_index("classification.family")
    collection.create_index("classification.phylum")

    logger.info(
        f"Successfully loaded {collection.count_documents({})} documents into MongoDB"
    )
    client.close()


#
# MAIN FUNCTION
#
def main():
    """Main ETL pipeline function."""
    try:
        logger.info("Starting Mushroom ETL Pipeline")

        # Extract data from CSV files
        dataframes = load_csv_files()

        # Transform data into MongoDB documents
        species_documents = transform_data(dataframes)

        # Load data into MongoDB
        if species_documents:
            load_to_mongodb(species_documents)
        else:
            logger.error("No species documents were created")

        logger.info("ETL Pipeline completed successfully")

    except Exception as e:
        logger.error(f"ETL Pipeline failed: {str(e)}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
