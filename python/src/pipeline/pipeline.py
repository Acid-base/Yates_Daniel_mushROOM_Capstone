from pymongo.errors import BulkWriteError
from pymongo import MongoClient
import os
import re
from typing import Callable, Dict, List
import logging
import numpy as np
import pandas as pd
import yaml

# Constants for file names and formats
CSV_FORMAT = "csv"
JSON_FORMAT = "json"

# Constants for data types
INT_TYPE = int
FLOAT_TYPE = float
BOOL_TYPE = bool
STR_TYPE = str

DATA_TYPES = {
    'int': int,
    'float': float,
    'bool': bool,
    'str': str
}

# Default values for missing data
DEFAULT_LAT = 0
DEFAULT_LNG = 0
DEFAULT_ALT = 0

DEFAULT_VALUES = {
    'lat': 0,
    'lng': 0,
    'alt': 0
}

# Mapping for license names
LICENSE_MAPPING = {
    "cc-by-sa-3.0": "CC BY-SA 3.0",
    "cc-by-nc-sa-2.0": "CC BY-NC-SA 2.0",
    "cc-by-nc-nd-2.0": "CC BY-NC-ND 2.0",
    "cc-by-nc-sa-2.5": "CC BY-NC-SA 2.5",
    "cc-by-sa-2.5": "CC BY-SA 2.5",
    "cc-by-nc-3.0": "CC BY-NC 3.0",
    "cc-by-2.0": "CC BY 2.0",
    "cc-by-sa-2.0": "CC BY-SA 2.0",
    "cc-by-nc-nd-3.0": "CC BY-NC-ND 3.0",
    "cc-by-nc-sa-3.0": "CC BY-NC-SA 3.0",
    "cc-by-nd-3.0": "CC BY-ND 3.0",
    "cc-by-nc-nd-2.5": "CC BY-NC-ND 2.5",
    "cc-by-sa-4.0": "CC BY-SA 4.0",
    "cc-by-nc-4.0": "CC BY-NC-SA 4.0",
    "cc-by-4.0": "CC BY 4.0",
    "cc0": "CC0 1.0 Universal",
}

# Function to load configuration
def load_config(config_file: str) -> dict:
    """Load configuration from a YAML file."""
    with open(config_file, 'r') as f:
        return yaml.safe_load(f)

# Function to set up logging
def setup_logging(config: dict) -> None:
    """Set up logging based on configuration."""
    logging.basicConfig(filename=config['log_file'], level=config['log_level'],
                        format='%(asctime)s - %(levelname)s - %(message)s')

# Function to clean text
def clean_text(text: str) -> str:
    """Remove HTML tags from text and strip whitespace."""
    return re.sub('<[^<]+?>', '', str(text)).strip()

# Function to clean a DataFrame
def clean_dataframe(df: pd.DataFrame, column_cleaners: Dict[str, Callable]) -> pd.DataFrame:
    """Clean a DataFrame by applying specified cleaning functions to columns."""
    return df.assign(**{col: cleaner(df[col]) for col, cleaner in column_cleaners.items() if col in df.columns})

# Function to clean names data
def clean_names(df: pd.DataFrame) -> pd.DataFrame:
    return clean_dataframe(df, {
        'text_name': clean_text,
        'author': lambda x: x.str.strip(),
        'deprecated': lambda x: x.astype(BOOL_TYPE)
    })

# Function to clean observations data
def clean_observations(df: pd.DataFrame) -> pd.DataFrame:
    logging.info("Data types before conversion:\n%s", df.dtypes.to_string())
    logging.info("\nSample 'when' column values before conversion:\n%s", df['when'].head(10).to_string())
    df['when'] = pd.to_datetime(df['when'], errors='coerce')
    logging.info("\nSample 'when' column values after conversion:\n%s", df['when'].head(10).to_string())
    return clean_dataframe(df, {
        'notes': clean_text,
        'lat': lambda x: x.fillna(DEFAULT_VALUES['lat']),
        'lng': lambda x: x.fillna(DEFAULT_VALUES['lng']),
        'alt': lambda x: x.fillna(DEFAULT_VALUES['alt'])
    })

# Function to clean images data
def clean_images(df: pd.DataFrame) -> pd.DataFrame:
    return clean_dataframe(df, {
        'copyright_holder': lambda x: x.str.strip(),
        'license': lambda x: x.str.lower().map(LICENSE_MAPPING).fillna(x)
    })

# Function to clean location descriptions data
def clean_location_descriptions(df: pd.DataFrame) -> pd.DataFrame:
    return clean_dataframe(df, {col: clean_text for col in ['gen_desc', 'ecology', 'species', 'notes', 'refs']})

# Function to clean locations data
def clean_locations(df: pd.DataFrame) -> pd.DataFrame:
    return clean_dataframe(df, {
        'name': clean_text,
        'city': lambda x: x.str.strip().str.lower(),
        'state': lambda x: x.str.strip().str.lower(),
        'country': lambda x: x.str.strip().str.lower()
    })

# Function to clean name descriptions data
def clean_name_descriptions(df: pd.DataFrame) -> pd.DataFrame:
    return clean_dataframe(df, {'description': clean_text})

# Function to load and clean a CSV file
def load_and_clean_csv(filename: str, cleaning_func: Callable[[pd.DataFrame], pd.DataFrame], converters: Dict[str, Callable]) -> pd.DataFrame:
    """
    Load a CSV file, apply converters, and clean the resulting DataFrame.

    Args:
        filename (str): The name of the CSV file to load.
        cleaning_func (Callable[[pd.DataFrame], pd.DataFrame]): A function to clean the loaded DataFrame.
        converters (Dict[str, Callable]): A dictionary of functions to convert values in certain columns.

    Returns:
        pd.DataFrame: The loaded, converted, and cleaned DataFrame.

    Raises:
        Exception: If there's an error processing the file.
    """
    separators = [',', ';', '\t', '|', ' ', '  ']
    for separator in separators:
        try:
            df = pd.read_csv(filename, sep=separator, header=0, low_memory=False,
                             converters=converters, na_values=['NULL'])
            cleaned_df = cleaning_func(df)
            log_data_types(cleaned_df, filename)
            return cleaned_df
        except Exception as e:
            logging.error(f"Error processing {filename} with separator '{separator}': {e}")
    logging.error(f"Failed to process {filename} with any of the separators: {separators}")
    return pd.DataFrame()

# Function to log data types
def log_data_types(df: pd.DataFrame, filename: str) -> None:
    logging.info(f"Data types for {filename}:\n%s", df.dtypes.to_string())

# Function to save a DataFrame
def save_dataframe(df: pd.DataFrame, filename: str, format: str = CSV_FORMAT) -> None:
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    if format == CSV_FORMAT:
        df.to_csv(filename, sep=',', index=False)
    elif format == JSON_FORMAT:
        df.to_json(filename, orient='records', lines=True)

# Function to safely convert a value to float
def safe_float_convert(x):
    try:
        return float(x)
    except ValueError:
        return np.nan

# Dictionary of converters for different CSV files
CONVERTERS = {
    "names.csv": {
        'id': int,
        'text_name': str,
        'author': str,
        'deprecated': lambda x: x.lower() == 'true',
        'correct_spelling_id': safe_float_convert,
        'synonym_id': safe_float_convert,
        'rank': INT_TYPE
    },
    "observations.csv": {
        'id': INT_TYPE,
        'name_id': INT_TYPE,
        'when': STR_TYPE,
        'is_collection_location': INT_TYPE,
        'thumb_image_id': safe_float_convert
    },
    "images.csv": {
        'id': INT_TYPE,
        'content_type': STR_TYPE,
        'copyright_holder': STR_TYPE,
        'license': STR_TYPE,
        'ok_for_export': INT_TYPE,
        'diagnostic': INT_TYPE
    },
    "location_descriptions.csv": {
        'id': STR_TYPE,
        'location_id': STR_TYPE,
        'source_type': STR_TYPE,
        'source_name': STR_TYPE,
        'gen_desc': STR_TYPE,
        'ecology': STR_TYPE,
        'species': STR_TYPE,
        'notes': STR_TYPE,
        'refs': STR_TYPE
    },
    "locations.csv": {
        'id': INT_TYPE,
        'name': STR_TYPE,
        'north': safe_float_convert,
        'south': safe_float_convert,
        'east': safe_float_convert,
        'west': safe_float_convert,
        'high': safe_float_convert,
        'low': safe_float_convert
    },
    "images_observations.csv": {
        'image_id': INT_TYPE,
        'observation_id': INT_TYPE
    },
    "name_classifications.csv": {
        'name_id': INT_TYPE,
        'domain': STR_TYPE,
        'kingdom': STR_TYPE,
        'phylum': STR_TYPE,
        'class': STR_TYPE,
        'order': STR_TYPE,
        'family': STR_TYPE
    },
    "name_descriptions.csv": {
        'id': STR_TYPE,
        'name_id': STR_TYPE,
        'source_type': STR_TYPE,
        'source_name': STR_TYPE,
        'general_description': STR_TYPE,
        'diagnostic_description': STR_TYPE,
        'distribution': STR_TYPE,
        'habitat': STR_TYPE,
        'look_alikes': STR_TYPE,
        'uses': STR_TYPE,
        'notes': STR_TYPE,
        'refs': STR_TYPE
    }
}

# Function to validate a DataFrame
def validate_dataframe(df: pd.DataFrame, expected_columns: list) -> bool:
    missing_columns = set(expected_columns) - set(df.columns)
    if missing_columns:
        logging.warning(f"Missing columns: {missing_columns}")
        return False
    return True

# Function to transform a DataFrame for upsert
def transform_for_upsert(df: pd.DataFrame) -> pd.DataFrame:
    return df.dropna()

# Function to compare two DataFrames
def diff_dataframes(df1: pd.DataFrame, df2: pd.DataFrame, filename: str, log_file: str) -> None:
    logging.info(f"Comparing dataframes for {filename}")

    df1 = df1.reset_index(drop=True)
    df2 = df2.reset_index(drop=True)
    df1, df2 = df1.align(df2, join='outer', axis=None)

    try:
        diff = df1.compare(df2)
        if not diff.empty:
            logging.info(f"Differences found in {filename}:", extra={'log_file': log_file})
            for col in diff.columns.get_level_values(0).unique():
                col_diff = diff[col]
                if not col_diff.empty:
                    logging.info(f"Column: {col}", extra={'log_file': log_file})
                    logging.info(col_diff.head(10).to_string(), extra={'log_file': log_file})
        else:
            logging.info(f"No differences found in {filename}", extra={'log_file': log_file})

    except ValueError as e:
        logging.error(f"Error comparing dataframes for {filename}: {str(e)}")
        logging.info("Falling back to manual comparison")

        diff = (df1 != df2) | (df1.isnull() ^ df2.isnull())
        if diff.any().any():
            logging.info(f"Differences found in {filename}:", extra={'log_file': log_file})
            for col in diff.columns:
                col_diff = diff[col]
                if col_diff.any():
                    logging.info(f"Column: {col}", extra={'log_file': log_file})
                    logging.info(col_diff.head(10).to_string(), extra={'log_file': log_file})
        else:
            logging.info(f"No differences found in {filename}", extra={'log_file': log_file})
# Function to connect to MongoDB
def connect_to_mongodb(config: dict) -> MongoClient:
    """
    Connect to MongoDB using the provided configuration.

    Args:
        config (dict): Configuration dictionary containing database connection details.

    Returns:
        MongoClient: MongoDB client connected to the specified database.
    """
    client = MongoClient(config['database']['host'],
                         config['database']['port'])
    return client[config['database']['name']]

# Function to upsert data to MongoDB
ddef upsert_to_mongodb(collection, data: list, key_field: str):
    """
    Perform an upsert operation on the specified MongoDB collection.

    Args:
        collection: MongoDB collection object.
        data (list): List of dictionaries containing the data to upsert.
        key_field (str): The field to use as the unique identifier for upsert operations.

    Raises:
        BulkWriteError: If there's an error during the bulk write operation.
    """
    try:
        operations = [
            {
                'update_one': {
                    'filter': {key_field: item[key_field]},
                    'update': {'$set': item},
                    'upsert': True
                }
            }
            for item in data
        ]
        result = collection.bulk_write(operations, ordered=False)
        logging.info(f"Upserted {result.upserted_count} documents, modified {result.modified_count} documents")
    except BulkWriteError as bwe:
        logging.error(f"Bulk write error: {bwe.details}")
        raise

# Function to preprocess all CSV files
def preprocess_all_csv_files():
    # Dictionary of cleaning functions for different CSV files
    file_cleaners = {
        "names.csv": clean_names,
        "observations.csv": clean_observations,
        "images.csv": clean_images,
        "location_descriptions.csv": clean_location_descriptions,
        "locations.csv": clean_locations,
        "images_observations.csv": lambda df: df,
        "name_classifications.csv": lambda df: df,
        "name_descriptions.csv": clean_name_descriptions
    }

    cleaned_dfs = {}
    for name, cleaner in file_cleaners.items():
        retries = 3
        while retries > 0:
            try:
                # Find the file configuration based on 'name'
                file_config = next((f for f in config['files'] if f['name'] == name), None)
                if file_config:
                    df = load_and_clean_csv(
                        file_config['input'],  # Access input path from file_config
                        cleaner,
                        CONVERTERS.get(name, {})
                    )
                    if not df.empty:
                        intermediate_filename = os.path.join(
                            config['intermediate_directory'], name)
                        save_dataframe(df, intermediate_filename)
                        cleaned_dfs[name] = df
                    break
                else:
                    logging.error(f"File configuration not found for {name}")
                    break
            except Exception as e:
                logging.error(f"Error processing {name}, retries left: {retries}", exc_info=True)
                retries -= 1
                if retries == 0:
                    logging.error(f"Failed to process {name} after 3 attempts")

    logging.info("Phase 1: Intermediate CSVs saved")

    db = connect_to_mongodb(config)

    for name, df in cleaned_dfs.items():
        file_config = next(
            (f for f in config['files'] if f['name'] == name), None)
        if file_config and validate_dataframe(df, file_config['columns']):
            transformed_df = transform_for_upsert(df)
            final_filename = os.path.join(
                config['output_directory'], file_config['output'])
            save_dataframe(transformed_df, final_filename, format=JSON_FORMAT)
            diff_dataframes(df, transformed_df, name, config['log_file'])

            # Upsert to MongoDB
            collection_name = name.replace('.csv', '')
            collection = db[collection_name]
            upsert_to_mongodb(collection, transformed_df.to_dict('records'), file_config['key_field'])

# Main execution block
if __name__ == "__main__":
    # Load configuration
    config = load_config('config.yaml')
    # Set up logging
    setup_logging(config)
    # Preprocess all CSV files
    preprocess_all_csv_files()
