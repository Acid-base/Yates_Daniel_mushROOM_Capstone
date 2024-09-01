from sqlite3 import converters
import pandas as pd
import numpy as np
import logging
from typing import Callable, Dict, Any
import re
import os
from pymongo import MongoClient
from pymongo.errors import BulkWriteError
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuration
CONFIG = {
    'database': {
        'host': 'localhost',
        'port': 27017,
        'name': 'your_database_name'
    },
    'log_file': 'data_processing.log',
    'intermediate_dir': 'intermediate',
    'final_dir': 'final'
}

# Set up logging
logging.basicConfig(filename=CONFIG['log_file'], level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define cleaning functions for each file type



def safe_float_convert(x: Any) -> float:
    try:
        return float(x)
    except (ValueError, TypeError):
        return np.nan



def clean_location_descriptions(df: pd.DataFrame) -> pd.DataFrame:
    df = clean_dataframe(df, {
        'gen_desc': lambda x: x.apply(clean_text),
        'ecology': lambda x: x.apply(clean_text),
        'species': lambda x: x.apply(clean_text),
        'notes': lambda x: x.apply(clean_text),
        'refs': lambda x: x.apply(clean_text)
    })
    df['id'] = pd.to_numeric(df['id'], errors='coerce').astype('Int64')
    return df

def clean_locations(df: pd.DataFrame) -> pd.DataFrame:
    df = clean_dataframe(df, {
        'name': safe_float_convert,
        'north': safe_float_convert,
        'south': safe_float_convert,
        'east': safe_float_convert,
        'west': safe_float_convert,
        'high': safe_float_convert,
        'low': safe_float_convert
    })
    df['id'] = pd.to_numeric(df['id'], errors='coerce').astype('Int64')
    return df

def load_and_clean_csv(filename: str, cleaning_func: Callable[[pd.DataFrame], pd.DataFrame], converters: Dict[str, Callable]) -> pd.DataFrame:
    try:
        df = pd.read_csv(filename, sep="\t", header=0, low_memory=False,
             converters=converters, na_values=['NULL'])
        cleaned_df = cleaning_func(df)
        if cleaned_df.empty:
            logger.warning(
                f"Cleaning resulted in an empty dataframe for {filename}")
            return pd.DataFrame()
        log_data_types(cleaned_df, filename)
        return cleaned_df
    except Exception as e:
        logger.error(f"Error processing {filename}: {e}")
        return pd.DataFrame()

def log_data_types(df: pd.DataFrame, filename: str) -> None:
    logger.info(f"Data types for {filename}:\n{df.dtypes.to_string()}\n")

def save_dataframe(df: pd.DataFrame, filename: str, format: str = 'csv') -> None:
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    if format == 'csv':
        df.to_csv(filename, sep="\t", index=False)
    elif format == 'json':
        df.to_json(filename, orient='records', lines=True)

def validate_dataframe(df: pd.DataFrame, expected_columns: list) -> bool:
    missing_columns = set(expected_columns) - set(df.columns)
    if missing_columns:
        logger.warning(f"Missing columns: {missing_columns}")
        return False
    return True




def diff_dataframes(df1: pd.DataFrame, df2: pd.DataFrame, filename: str) -> None:
    logger.info(f"Comparing dataframes for {filename}")
    df1 = df1.reset_index(drop=True)
    df2 = df2.reset_index(drop=True)
    df1, df2 = df1.align(df2, join='outer', axis=None)
    try:
        diff = df1.compare(df2)
        if not diff.empty:
            logger.info(f"Differences found in {filename}:")
            for col in diff.columns.get_level_values(0).unique():
                col_diff = diff[col]
                if not col_diff.empty:
                    logger.info(
                        f"Column: {col}\n{col_diff.head(10).to_string()}")
        else:
            logger.info(f"No differences found in {filename}")
    except ValueError as e:
        logger.error(f"Error comparing dataframes for {filename}: {str(e)}")
        logger.info("Falling back to manual comparison")
        diff = (df1 != df2) | (df1.isnull() ^ df2.isnull())
        if diff.any().any():
            logger.info(f"Differences found in {filename}:")
            for col in diff.columns:
                if diff[col].any():
                    logger.info(
                        f"Column: {col}\n{df1[diff[col]][col].head(10).to_string()}")
        else:
            logger.info(f"No differences found in {filename}")
def process_file(name: str, cleaner: Callable, converters: Dict[str, Callable], expected_columns: list) -> None:
    logger.info(f"Processing {name}")
    df = load_and_clean_csv(name, cleaner, converters)
    if not df.empty and validate_dataframe(df, expected_columns):
        transformed_df = transform_for_upsert(df)
        logger.info(f"Original dataframe for {name}:\n{df.head().to_string()}")
        logger.info(f"Transformed dataframe for {name}:\n{transformed_df.head().to_string()}")

        if transformed_df.empty:
            logger.warning(f"Transformed dataframe for {name} is empty. Skipping upsert.")
            return

        intermediate_filename = os.path.join(CONFIG['intermediate_dir'], name)
        save_dataframe(df, intermediate_filename)

        final_filename = os.path.join(CONFIG['final_dir'], name.replace('.csv', '.json'))
        save_dataframe(transformed_df, final_filename, format='json')

        diff_dataframes(df, transformed_df, name)

        db = connect_to_mongodb(CONFIG['database'])
        collection = db[name.replace('.csv', '')]
        try:
            upsert_to_mongodb(collection, transformed_df.to_dict('records'), 'id')
        except Exception as e:
            logger.error(f"Error upserting to MongoDB for {name}: {e}")
    else:
        logger.warning(f"Validation failed for {name}. Skipping transformation.")
def transform_for_upsert(df: pd.DataFrame) -> pd.DataFrame:
    df = df.dropna(subset=['id'])
    df = df.where(pd.notnull(df), None)  # Convert NaN to None
    return df

def clean_text(text: str, max_length: int = 1000) -> str:
    cleaned_text = re.sub('<[^<]+?>', '', str(text)).strip()
    return cleaned_text[:max_length] if len(cleaned_text) > max_length else cleaned_text

def clean_dataframe(df: pd.DataFrame, column_cleaners: Dict[str, Callable]) -> pd.DataFrame:
    return df.assign(**{col: cleaner(df[col]) for col, cleaner in column_cleaners.items() if col in df.columns})

def clean_location_descriptions(df: pd.DataFrame) -> pd.DataFrame:
    df = clean_dataframe(df, {
        'gen_desc': lambda x: x.apply(clean_text),
        'ecology': lambda x: x.apply(clean_text),
        'species': lambda x: x.apply(clean_text),
        'notes': lambda x: x.apply(clean_text),
        'refs': lambda x: x.apply(clean_text)
    })
    df['id'] = pd.to_numeric(df['id'], errors='coerce').astype('Int64')
    return df

def clean_names(df: pd.DataFrame) -> pd.DataFrame:
    df = clean_dataframe(df, {
        'text_name': lambda x: x.apply(clean_text),
        'author': lambda x: x.str.strip(),
        'deprecated': lambda x: x.astype(bool)
    })
    df['id'] = pd.to_numeric(df['id'], errors='coerce').astype('Int64')
    return df

def clean_observations(df: pd.DataFrame) -> pd.DataFrame:
    df['when'] = pd.to_datetime(df['when'], errors='coerce')
    return clean_dataframe(df, {
        'notes': lambda x: x.apply(clean_text),
        'lat': safe_float_convert,
        'lng': safe_float_convert,
        'alt': safe_float_convert
    })

def clean_locations(df: pd.DataFrame) -> pd.DataFrame:
    df = clean_dataframe(df, {
        'name': lambda x: x.apply(clean_text),
        'north': safe_float_convert,
        'south': safe_float_convert,
        'east': safe_float_convert,
        'west': safe_float_convert,
        'high': safe_float_convert,
        'low': safe_float_convert
    })
    df['id'] = pd.to_numeric(df['id'], errors='coerce').astype('Int64')
    return df

def clean_name_descriptions(df: pd.DataFrame) -> pd.DataFrame:
    df = clean_dataframe(df, {
        'general_description': lambda x: x.apply(clean_text),
        'diagnostic_description': lambda x: x.apply(clean_text),
        'distribution': lambda x: x.apply(clean_text),
        'habitat': lambda x: x.apply(clean_text),
        'look_alikes': lambda x: x.apply(clean_text),
        'uses': lambda x: x.apply(clean_text),
        'notes': lambda x: x.apply(clean_text),
        'refs': lambda x: x.apply(clean_text)
    })
    df['id'] = pd.to_numeric(df['id'], errors='coerce').astype('Int64')
    return df

def process_file(name: str, cleaner: Callable, converters: Dict[str, Callable], expected_columns: list) -> None:
    logger.info(f"Processing {name}")
    df = load_and_clean_csv(name, cleaner, converters)
    if not df.empty and validate_dataframe(df, expected_columns):
        transformed_df = transform_for_upsert(df)
        logger.info(f"Original dataframe for {name}:\n{df.head().to_string()}")
        logger.info(f"Transformed dataframe for {name}:\n{transformed_df.head().to_string()}")

        if transformed_df.empty:
            logger.warning(f"Transformed dataframe for {name} is empty. Skipping upsert.")
            return

        intermediate_filename = os.path.join(CONFIG['intermediate_dir'], name)
        save_dataframe(df, intermediate_filename)

        final_filename = os.path.join(CONFIG['final_dir'], name.replace('.csv', '.json'))
        save_dataframe(transformed_df, final_filename, format='json')

        diff_dataframes(df, transformed_df, name)

        db = connect_to_mongodb(CONFIG['database'])
        collection = db[name.replace('.csv', '')]
        upsert_to_mongodb(collection, transformed_df.to_dict('records'), 'id')
    else:
        logger.warning(f"Validation failed for {name}. Skipping transformation.")


def connect_to_mongodb(config: dict) -> MongoClient:
    client = MongoClient(config['host'], config['port'])
    return client[config['name']]

def upsert_to_mongodb(collection, data: list, key_field: str):
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
        logger.info(
            f"Upserted {result.upserted_count} documents, modified {result.modified_count} documents")
    except BulkWriteError as bwe:
        logger.error(f"Bulk write error: {bwe.details}")
        raise

def process_file(name: str, cleaner: Callable, converters: Dict[str, Callable], expected_columns: list) -> None:
    logger.info(f"Processing {name}")
    df = load_and_clean_csv(name, cleaner, converters)
    if not df.empty and validate_dataframe(df, expected_columns):
        transformed_df = transform_for_upsert(df)
        logger.info(f"Original dataframe for {name}:\n{df.head().to_string()}")
        logger.info(
            f"Transformed dataframe for {name}:\n{transformed_df.head().to_string()}")

        if transformed_df.empty:
            logger.warning(
                f"Transformed dataframe for {name} is empty. Skipping upsert.")
            return

        intermediate_filename = os.path.join(CONFIG['intermediate_dir'], name)
        save_dataframe(df, intermediate_filename)

        final_filename = os.path.join(
            CONFIG['final_dir'], name.replace('.csv', '.json'))
        save_dataframe(transformed_df, final_filename, format='json')

        diff_dataframes(df, transformed_df, name)

        db = connect_to_mongodb(CONFIG['database'])
        collection = db[name.replace('.csv', '')]
        upsert_to_mongodb(collection, transformed_df.to_dict('records'), 'id')
    else:
        logger.warning(
            f"Validation failed for {name}. Skipping transformation.")
def preprocess_all_csv_files():
    file_cleaners = {
        "names.csv": clean_names,
        "observations.csv": clean_observations,
        "images.csv": clean_names,
        "location_descriptions.csv": clean_location_descriptions,
        "locations.csv": clean_locations,
        "images_observations.csv": lambda df: df,
        "name_classifications.csv": lambda df: df,
        "name_descriptions.csv": clean_name_descriptions
    }

    expected_columns = {
        "names.csv": ['id', 'text_name', 'author'],
        "observations.csv": ['id', 'name_id', 'when', 'location_id'],
        "images.csv": ['id', 'content_type', 'copyright_holder', 'license', 'ok_for_export', 'diagnostic'],
        "location_descriptions.csv": ['id', 'location_id', 'source_type', 'source_name', 'gen_desc', 'ecology', 'species', 'notes', 'refs'],
        "locations.csv": ['id', 'name', 'north', 'south', 'east', 'west', 'high', 'low'],
        "images_observations.csv": ['image_id', 'observation_id'],
        "name_classifications.csv": ['name_id', 'domain', 'kingdom', 'phylum', 'class', 'order', 'family'],
        "name_descriptions.csv": ['id', 'name_id', 'source_type', 'source_name', 'general_description', 'diagnostic_description', 'distribution', 'habitat', 'look_alikes', 'uses', 'notes', 'refs']
    }

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [
            executor.submit(process_file, name, cleaner, converters.get(
                name, {}), expected_columns.get(name, []))
            for name, cleaner in file_cleaners.items()
        ]

        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                logger.error(f"Error in thread: {e}")
    logger.info("All CSV files preprocessed to JSON successfully!")

if __name__ == "__main__":
    preprocess_all_csv_files()
