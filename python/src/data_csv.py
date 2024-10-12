from __future__ import annotations

import logging
import os
import re
from typing import Any, Callable

import pandas as pd

# Configuration
CONFIG = {
    "database": {"host": "localhost", "port": 27017, "name": "your_database_name"},
    "log_file": "data_processing.log",
    "intermediate_dir": "intermediate",
    "final_dir": "final",
}

# Set up logging
logging.basicConfig(
    filename=CONFIG["log_file"],
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Define cleaning functions
def safe_float_convert(x: Any) -> float:
    """Converts a value to a float, handling errors gracefully."""
    try:
        return float(x)
    except (ValueError, TypeError):
        return float("nan")


def clean_text(text: str, max_length: int = 1000) -> str:
    """Cleans text by removing HTML tags and limiting length."""
    cleaned_text = re.sub("<[^<]+?>", "", str(text)).strip()
    return cleaned_text[:max_length]


def clean_dataframe(
    df: pd.DataFrame, column_cleaners: dict[str, Callable],
) -> pd.DataFrame:
    """Cleans a DataFrame by applying cleaning functions to columns."""
    return df.assign(
        **{
            col: cleaner(df[col])
            for col, cleaner in column_cleaners.items()
            if col in df.columns
        },
    )


def clean_names(df: pd.DataFrame) -> pd.DataFrame:
    """Cleans names in a DataFrame."""
    return clean_dataframe(
        df,
        {
            "text_name": lambda x: x.apply(clean_text),
            "author": lambda x: x.str.strip(),
            "deprecated": lambda x: x.astype(bool),
        },
    ).assign(id=pd.to_numeric(df["id"], errors="coerce").astype("Int64"))


def clean_observations(df: pd.DataFrame) -> pd.DataFrame:
    """Cleans observations in a DataFrame."""
    df["when"] = pd.to_datetime(df["when"], errors="coerce")
    return clean_dataframe(
        df,
        {
            "notes": lambda x: x.apply(clean_text),
            "lat": safe_float_convert,
            "lng": safe_float_convert,
            "alt": safe_float_convert,
        },
    )


def clean_location_descriptions(df: pd.DataFrame) -> pd.DataFrame:
    """Cleans location descriptions in a DataFrame."""
    return clean_dataframe(
        df,
        {
            "gen_desc": lambda x: x.apply(clean_text),
            "ecology": lambda x: x.apply(clean_text),
            "species": lambda x: x.apply(clean_text),
            "notes": lambda x: x.apply(clean_text),
            "refs": lambda x: x.apply(clean_text),
        },
    ).assign(id=pd.to_numeric(df["id"], errors="coerce").astype("Int64"))


def clean_locations(df: pd.DataFrame) -> pd.DataFrame:
    """Cleans location data in a DataFrame."""
    return clean_dataframe(
        df,
        {
            "name": lambda x: x.apply(clean_text),
            "north": safe_float_convert,
            "south": safe_float_convert,
            "east": safe_float_convert,
            "west": safe_float_convert,
            "high": safe_float_convert,
            "low": safe_float_convert,
        },
    ).assign(id=pd.to_numeric(df["id"], errors="coerce").astype("Int64"))


def clean_name_descriptions(df: pd.DataFrame) -> pd.DataFrame:
    """Cleans name descriptions in a DataFrame."""
    return clean_dataframe(
        df,
        {
            "general_description": lambda x: x.apply(clean_text),
            "diagnostic_description": lambda x: x.apply(clean_text),
            "distribution": lambda x: x.apply(clean_text),
            "habitat": lambda x: x.apply(clean_text),
            "look_alikes": lambda x: x.apply(clean_text),
            "uses": lambda x: x.apply(clean_text),
            "notes": lambda x: x.apply(clean_text),
            "refs": lambda x: x.apply(clean_text),
        },
    ).assign(id=pd.to_numeric(df["id"], errors="coerce").astype("Int64"))


def load_and_clean_csv(
    filename: str, cleaning_func: Callable[[pd.DataFrame], pd.DataFrame],
) -> pd.DataFrame:
    """Loads a CSV file, cleans it, and returns a DataFrame."""
    try:
        df = pd.read_csv(
            filename, sep="\t", header=0, low_memory=False, na_values=["NULL"],
        )
        cleaned_df = cleaning_func(df)
        if cleaned_df.empty:
            logger.warning(f"Cleaning resulted in an empty dataframe for {filename}")
            return pd.DataFrame()
        log_data_types(cleaned_df, filename)
        return cleaned_df
    except Exception as e:
        logger.exception(f"Error processing {filename}: {e}")
        return pd.DataFrame()


def log_data_types(df: pd.DataFrame, filename: str) -> None:
    """Logs the data types of a DataFrame."""
    logger.info(f"Data types for {filename}:\n{df.dtypes.to_string()}\n")


def save_dataframe(df: pd.DataFrame, filename: str, format: str = "csv") -> None:
    """Saves a DataFrame to a file."""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    if format == "csv":
        df.to_csv(filename, sep="\t")
