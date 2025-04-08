"""CSV data processing and validation module."""

import csv
import io
import logging
import re
from pathlib import Path
from typing import Any, Dict, Generator, Iterator, List, Optional, Type, TypeVar

import numpy as np
import pandas as pd
from pydantic import ValidationError
from schemas import (
    BaseModel,
    ImageSchema,
    ImagesObservationSchema,
    LocationDescriptionSchema,
    LocationSchema,
    NameClassificationSchema,
    NameDescriptionSchema,
    NameSchema,
    ObservationSchema,
    validate_record,
)

logger = logging.getLogger(__name__)

# Remove any delimiter settings from DEFAULT_PARAMS
DEFAULT_PARAMS = {
    "dtype": str,
    "na_values": ["", "NULL", "null", "NA", "N/A", "n/a", "None", "none"],
    "keep_default_na": True,
    "encoding": "utf-8",
    "chunksize": 1000,
    "encoding_errors": "replace",
    "on_bad_lines": "skip",  # Always skip bad lines - updated from warn_bad_lines
}

# License mapping for image files
LICENSE_MAPPING = {
    "Creative Commons Wikipedia Compatible v3.0": 1,
    "CC BY-SA": 2,
    "CC BY": 3,
    "Public Domain": 4,
    "All Rights Reserved": 5,
}

# Schema mapping for validation
T = TypeVar("T", bound=BaseModel)


class CSVProcessor:
    """Process CSV files with configurable options."""

    def __init__(self, config: Any):
        """Initialize CSV processor with configuration."""
        self.config = config
        self._setup_csv_params()
        self.errors = []
        self._setup_schema_mapping()

    def _setup_csv_params(self) -> None:
        """Set up CSV processing parameters."""
        self.csv_params = DEFAULT_PARAMS.copy()

        # Add any CSV-specific config from environment
        if hasattr(self.config, "NULL_VALUES"):
            self.csv_params["na_values"] = self.config.NULL_VALUES

        if hasattr(self.config, "BATCH_SIZE"):
            self.csv_params["chunksize"] = self.config.BATCH_SIZE

    def _setup_schema_mapping(self) -> None:
        """Set up mapping of CSV file names to schema classes."""
        # This ensures the right schema is used for each file type
        self.schema_mapping = {
            "observations": ObservationSchema,
            "names": NameSchema,
            "name_descriptions": NameDescriptionSchema,
            "locations": LocationSchema,
            "location_descriptions": LocationDescriptionSchema,
            "images": ImageSchema,
            "images_observations": ImagesObservationSchema,
            "name_classifications": NameClassificationSchema,
        }

    def process_file(
        self, file_path: Path, table_name: str, **kwargs
    ) -> Generator[pd.DataFrame, None, None]:
        """Process CSV file with validation and transformations."""
        if not file_path.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")

        try:
            # For names.csv, we need special preprocessing
            if table_name == "names":
                # Set pandas display options to handle wide tables
                pd.set_option("display.max_columns", None)
                pd.set_option("display.width", None)

                # Add defaults for required fields
                required_fields = {
                    "text_name": "",
                    "search_name": "",
                    "display_name": "",
                    "sort_name": "",
                    "author": None,
                    "citation": None,
                    "deprecated": False,
                    "correct_spelling_id": None,
                    "synonym_id": None,
                    "rank": 0,
                    "notes": None,
                    "ok_for_export": True,
                    "classification": None,
                }
                kwargs.setdefault("dtype", required_fields)

            # Process file in chunks
            for chunk in self.read_chunks(file_path, **kwargs):
                if chunk is not None and not chunk.empty:
                    # Fill missing columns for names.csv
                    if table_name == "names":
                        for col, default in required_fields.items():
                            if col not in chunk.columns:
                                chunk[col] = default

                    # Process and validate chunk
                    processed_chunk = self._process_chunk(chunk, table_name)
                    if not processed_chunk.empty:
                        yield processed_chunk

        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            raise

    def read_chunks(
        self, file_path: Path, **kwargs
    ) -> Iterator[Optional[pd.DataFrame]]:
        """Read CSV file in chunks with robust handling of different formats.

        Enhanced to properly handle tab-separated files with embedded newlines.
        Follows the recommendations from the data analysis document for complex TSV files.

        Args:
            file_path: Path to the file to read
            **kwargs: Additional parameters for pandas.read_csv

        Returns:
            Iterator of DataFrames containing file chunks
        """
        try:
            # Merge default params with any provided kwargs
            params = self.csv_params.copy()

            # Convert 'delimiter' to 'sep' if provided
            if "delimiter" in kwargs and "sep" not in kwargs:
                kwargs["sep"] = kwargs.pop("delimiter")

            # Get file type and apply appropriate handling
            file_path_str = str(file_path)

            # Identify complex TSV files with embedded newlines
            complex_tsv = (
                "name_descriptions.csv" in file_path_str
                or "location_descriptions.csv" in file_path_str
            )

            # Special handling based on file type
            if "names.csv" in file_path_str:
                # Special handling for names.csv - known to be tab-separated
                names_params = {
                    "sep": "\t",  # Tab separated
                    "header": 0,  # First row contains headers
                    "dtype": str,  # Read everything as string first
                    "na_values": self.csv_params["na_values"],
                    "keep_default_na": True,
                    "on_bad_lines": "skip",  # Skip bad lines silently
                }
                params.update(names_params)
            elif "locations.csv" in file_path_str:
                # Special handling for locations.csv with quoting issues
                locations_params = {
                    "sep": "\t",  # Tab separated
                    "header": 0,  # First row contains headers
                    "quoting": 3,  # csv.QUOTE_NONE
                    "engine": "python",  # Python engine for better handling of embedded newlines
                    "encoding": "utf-8",
                    "encoding_errors": "replace",
                    "on_bad_lines": "skip",
                }
                params.update(locations_params)
            elif complex_tsv:
                # Special handling for files with complex embedded newlines
                # For name_descriptions.csv and location_descriptions.csv
                if kwargs.get("delimiter") == "\n" or kwargs.get("sep") == "\n":
                    # If caller wants newline-delimited format, use special handling
                    return self._read_special_format_file(file_path, params)
                else:
                    # Use recommended approach from the documentation for complex TSV files
                    complex_params = {
                        "sep": "\t",
                        "quotechar": '"',  # Double-quote as quote character
                        "quoting": csv.QUOTE_MINIMAL,  # Use quoting for fields containing delimiter or quotechar
                        "engine": "python",  # Python engine for better handling of embedded newlines
                        "encoding": "utf-8",
                        "encoding_errors": "replace",
                        "on_bad_lines": "skip",
                    }
                    params.update(complex_params)
            else:
                # Standard tab-separated files
                if "delimiter" not in kwargs and "sep" not in kwargs:
                    # Default to tab for most CSV files in this project
                    kwargs["sep"] = "\t"
                params.update(kwargs)

            # Always ensure deprecated parameters are removed
            if "warn_bad_lines" in params:
                del params["warn_bad_lines"]
            if "error_bad_lines" in params:
                del params["error_bad_lines"]

            try:
                logger.debug(f"Reading file {file_path} with params: {params}")
                # Try using read_csv with the specified parameters
                for chunk in pd.read_csv(file_path, **params):
                    if chunk is not None and not chunk.empty:
                        # Process file-specific chunks
                        if "locations.csv" in file_path_str:
                            chunk = self._process_locations_chunk(chunk)
                        yield chunk
            except Exception as e:
                logger.warning(
                    f"Error reading {file_path} with pandas: {e}. Trying alternative methods..."
                )

                # For complex TSV files with embedded newlines, try alternative parsing
                if complex_tsv:
                    logger.debug("Trying special format file handling for complex TSV")
                    yield from self._read_special_format_file(file_path, params)
                else:
                    # For simple TSV files, try manual parsing as last resort
                    logger.debug("Trying manual TSV parsing")
                    yield from self._manual_parse_tsv(file_path)

        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            yield None

    def _process_names_chunk(self, chunk: pd.DataFrame) -> pd.DataFrame:
        """Special processing for names.csv chunks."""
        try:
            # Ensure required fields exist
            required_fields = ["id", "text_name"]
            if not all(field in chunk.columns for field in required_fields):
                missing = [f for f in required_fields if f not in chunk.columns]
                logger.error(f"Missing required fields in names.csv: {missing}")
                return pd.DataFrame()

            # Add derived fields
            if "display_name" not in chunk.columns:
                chunk["display_name"] = chunk["text_name"]
            if "search_name" not in chunk.columns:
                chunk["search_name"] = chunk["text_name"].str.lower()
            if "sort_name" not in chunk.columns:
                chunk["sort_name"] = chunk["text_name"]

            # Set default values for optional fields
            chunk["deprecated"] = chunk.get("deprecated", False)
            chunk["ok_for_export"] = chunk.get("ok_for_export", True)
            chunk["rank"] = pd.to_numeric(chunk.get("rank", 4), errors="coerce").fillna(
                4
            )

            # Convert values
            for bool_field in ["deprecated", "ok_for_export"]:
                if bool_field in chunk.columns:
                    chunk[bool_field] = chunk[bool_field].map(
                        lambda x: str(x).lower() in ("true", "1", "t", "yes")
                    )

            for int_field in ["id", "synonym_id", "correct_spelling_id", "rank"]:
                if int_field in chunk.columns:
                    chunk[int_field] = pd.to_numeric(chunk[int_field], errors="coerce")

            # Apply schema validation to each record
            valid_records = []
            for _, row in chunk.iterrows():
                record = row.to_dict()
                validated_record = self.validate_record_against_schema(record, "names")
                if validated_record:
                    valid_records.append(validated_record)

            return pd.DataFrame(valid_records) if valid_records else pd.DataFrame()

        except Exception as e:
            logger.error(f"Error processing names chunk: {e}")
            return pd.DataFrame()

    def _process_locations_chunk(self, chunk: pd.DataFrame) -> pd.DataFrame:
        """Special processing for locations.csv chunks."""
        try:
            # Ensure required fields exist
            required_fields = ["id", "name"]
            if not all(field in chunk.columns for field in required_fields):
                missing = [f for f in required_fields if f not in chunk.columns]
                logger.error(f"Missing required fields in locations.csv: {missing}")
                return pd.DataFrame()

            # Convert coordinates to float
            for field in ["north", "south", "east", "west"]:
                if field in chunk.columns:
                    chunk[field] = pd.to_numeric(chunk[field], errors="coerce")

            # Convert elevation to int
            for field in ["high", "low"]:
                if field in chunk.columns:
                    chunk[field] = pd.to_numeric(chunk[field], errors="coerce")

            # Clean location names
            if "name" in chunk.columns:
                chunk["name"] = chunk["name"].apply(
                    lambda x: " ".join(str(x).split()) if pd.notna(x) else None
                )

            # Apply schema validation to each record
            valid_records = []
            for _, row in chunk.iterrows():
                record = row.to_dict()
                validated_record = self.validate_record_against_schema(
                    record, "locations"
                )
                if validated_record:
                    valid_records.append(validated_record)

            return pd.DataFrame(valid_records) if valid_records else pd.DataFrame()

        except Exception as e:
            logger.error(f"Error processing locations chunk: {e}")
            return pd.DataFrame()

    def _read_special_format_file(
        self, file_path: Path, params: Dict[str, Any]
    ) -> Iterator[pd.DataFrame]:
        """Handle special format files like name_descriptions.csv and location_descriptions.csv.

        These files have tab-separated columns with embedded newlines within the text fields.
        This method implements the recommended approach from the data analysis document:
        1. Using csv.reader with proper quoting settings to handle embedded newlines
        2. Falling back to custom parsing if the CSV reader fails

        Args:
            file_path: Path to the special format file
            params: Parameters for parsing

        Returns:
            Iterator of DataFrames with parsed records
        """
        try:
            logger.info(f"Reading special format file: {file_path}")
            file_name = file_path.name.lower()

            # Determine if this is a name_descriptions or location_descriptions file
            is_name_desc = "name_descriptions" in file_name
            is_location_desc = "location_descriptions" in file_name

            if not (is_name_desc or is_location_desc):
                logger.warning(
                    f"File {file_path} is not recognized as a special format file"
                )
                yield pd.DataFrame()
                return

            # First try the recommended approach - read as TSV with quoted fields
            try:
                logger.debug("Attempting to read as TSV with quoted fields")

                # Define expected headers based on file type
                if is_name_desc:
                    expected_headers = [
                        "id",
                        "name_id",
                        "source_type",
                        "source_name",
                        "gen_desc",
                        "diag_desc",
                        "distribution",
                        "habitat",
                        "look_alikes",
                        "uses",
                        "notes",
                        "refs",
                    ]
                else:  # location_descriptions
                    expected_headers = [
                        "id",
                        "location_id",
                        "source_type",
                        "source_name",
                        "gen_desc",
                        "ecology",
                        "species",
                        "notes",
                        "refs",
                    ]

                # Use the improved CSV reader approach with proper quoting
                batch_size = params.get("chunksize", 1000)
                records = []

                # Read the full content first - needed because of embedded newlines
                with open(
                    file_path,
                    "r",
                    encoding=params.get("encoding", "utf-8"),
                    errors=params.get("encoding_errors", "replace"),
                ) as f:
                    file_content = f.read()

                # Process the file content using Python's csv module
                csv_reader = csv.reader(
                    io.StringIO(file_content),
                    delimiter="\t",
                    quotechar='"',
                    quoting=csv.QUOTE_MINIMAL,
                )

                # Process header row
                try:
                    header = next(csv_reader)
                    # If header is shorter than expected, use expected headers
                    if len(header) < len(expected_headers):
                        logger.warning(
                            f"Header length {len(header)} less than expected {len(expected_headers)}. Using expected headers."
                        )
                        header = expected_headers
                except StopIteration:
                    logger.warning("Empty file or header row missing")
                    header = expected_headers

                # Process data rows
                for row in csv_reader:
                    if not row:
                        continue

                    record = {}
                    # Map values to header names
                    for i, field in enumerate(row):
                        if i < len(header):
                            field_name = header[i]
                            # Handle empty fields and NULL values
                            if not field or field.upper() == "NULL":
                                record[field_name] = None
                            else:
                                record[field_name] = field

                            # Convert numeric ID fields to integers
                            if (
                                field_name in ["id", "name_id", "location_id"]
                                and record[field_name]
                            ):
                                try:
                                    record[field_name] = int(record[field_name])
                                except (ValueError, TypeError):
                                    logger.warning(
                                        f"Invalid {field_name} value: {record[field_name]}"
                                    )

                    # Add record if it has valid ID fields
                    if any(
                        k in record and record[k]
                        for k in ["id", "name_id", "location_id"]
                    ):
                        records.append(record)

                        # Yield batch when we reach batch size
                        if len(records) >= batch_size:
                            yield pd.DataFrame(records)
                            records = []

                # Yield any remaining records
                if records:
                    yield pd.DataFrame(records)

            except Exception as e:
                logger.warning(f"Failed to read as TSV with quoted fields: {e}")
                # Fall back to legacy approach - line-by-line processing
                logger.debug("Falling back to line-by-line processing")

                # Set a smaller chunk size for special format files to prevent memory issues
                chunksize = min(params.get("chunksize", 1000), 500)

                # Read file in chunks rather than all at once to prevent memory issues
                with open(
                    file_path,
                    "r",
                    encoding=params.get("encoding", "utf-8"),
                    errors=params.get("encoding_errors", "replace"),
                ) as f:
                    # Process in manageable chunks of lines
                    records = []
                    current_record = {}
                    record_count = 0
                    line_count = 0
                    chunk_line_limit = 50000  # Process 50K lines at a time

                    # Read and process the file in chunks
                    while True:
                        chunk_lines = []
                        for _ in range(chunk_line_limit):
                            line = f.readline()
                            if not line:  # EOF reached
                                break
                            chunk_lines.append(line)
                            line_count += 1

                        if not chunk_lines:  # No more lines to process
                            break

                        # Process this chunk of lines
                        i = 0
                        while i < len(chunk_lines):
                            line = chunk_lines[i].strip()
                            i += 1

                            # Empty line - record separator
                            if not line:
                                if current_record and any(
                                    k in current_record
                                    for k in ["id", "name_id", "location_id"]
                                ):
                                    records.append(current_record)
                                    current_record = {}
                                    record_count += 1

                                    # Yield batch when we reach chunk size
                                    if record_count >= chunksize:
                                        logger.debug(
                                            f"Yielding {record_count} records from special format file"
                                        )
                                        df = pd.DataFrame(records)
                                        yield df
                                        records = []
                                        record_count = 0
                                continue

                            # Check if this is a field name line (contains colon)
                            if ":" in line:
                                parts = line.split(":", 1)
                                field_name = parts[0].strip().lower()
                                value = parts[1].strip() if len(parts) > 1 else ""

                                # For multi-line fields, look ahead and concatenate next lines until empty line
                                while (
                                    i < len(chunk_lines)
                                    and chunk_lines[i].strip()
                                    and ":" not in chunk_lines[i]
                                ):
                                    value += "\n" + chunk_lines[i].strip()
                                    i += 1

                                # Store field in current record
                                current_record[field_name] = value

                                # Track ID fields for record identification
                                if field_name in ["id", "name_id", "location_id"]:
                                    try:
                                        current_record[field_name] = int(value)
                                    except (ValueError, TypeError):
                                        pass

                    logger.debug(
                        f"Processed {line_count} lines from special format file"
                    )

                # Add the last record if any
                if current_record and any(
                    k in current_record for k in ["id", "name_id", "location_id"]
                ):
                    records.append(current_record)

                # Return any remaining records
                if records:
                    logger.debug(
                        f"Yielding final {len(records)} records from special format file"
                    )
                    df = pd.DataFrame(records)
                    yield df
                else:
                    yield pd.DataFrame()  # Empty DataFrame if no records

        except Exception as e:
            logger.error(f"Error reading special format file {file_path}: {e}")
            yield pd.DataFrame()

    def _process_chunk(self, chunk: pd.DataFrame, table_name: str) -> pd.DataFrame:
        """Process a chunk of CSV data with validation and transformation."""
        try:
            # Clean text fields
            text_columns = chunk.select_dtypes(include=["object"]).columns
            for col in text_columns:
                chunk[col] = chunk[col].apply(self._clean_text)

            # Special handling for specific tables
            if table_name == "images":
                chunk = self._process_images_chunk(chunk)
            elif table_name == "name_classifications":
                records = self._standardize_classifications(chunk.to_dict("records"))
                chunk = pd.DataFrame.from_records(records)
            elif table_name == "descriptions":
                chunk = self._process_description_chunk(chunk)
            elif table_name == "locations":
                chunk = self._process_locations_chunk(chunk)
            elif table_name == "names":
                chunk = self._process_names_chunk(chunk)

            # Clean numeric values
            numeric_columns = chunk.select_dtypes(include=[np.number]).columns
            for col in numeric_columns:
                chunk[col] = chunk[col].apply(self._clean_value)

            # Apply schema validation if a schema exists for this table
            if table_name in self.schema_mapping:
                # Convert DataFrame to list of records for validation
                records_to_validate = chunk.to_dict("records")
                valid_records = []

                # Validate each record
                for record in records_to_validate:
                    validated_record = self.validate_record_against_schema(
                        record, table_name
                    )
                    if validated_record:  # Only include records that pass validation
                        valid_records.append(validated_record)

                # Create a new DataFrame with validated records
                if valid_records:
                    logger.info(
                        f"Validated {len(valid_records)} records for {table_name}"
                    )
                    return pd.DataFrame(valid_records)
                else:
                    logger.warning(
                        f"No valid records found for {table_name} after validation"
                    )
                    return pd.DataFrame()

            return chunk

        except Exception as e:
            logger.error(f"Error processing chunk: {e}")
            return pd.DataFrame()

    def _process_images_chunk(self, chunk: pd.DataFrame) -> pd.DataFrame:
        """Process images data with special handling."""
        try:
            valid_records = []
            for _, row in chunk.iterrows():
                try:
                    record = row.to_dict()

                    # Handle license mapping - convert license string to license_id
                    license_id = None
                    if "license_id" in record:
                        license_id = record["license_id"]
                    elif "license" in record:
                        license_str = (
                            str(record["license"]).strip()
                            if pd.notna(record.get("license"))
                            else ""
                        )
                        license_id = LICENSE_MAPPING.get(license_str)
                        # Try case-insensitive match if exact match fails
                        if license_id is None:
                            for license_key, license_val in LICENSE_MAPPING.items():
                                if license_str.lower() == license_key.lower():
                                    license_id = license_val
                                    break
                        # Default to license ID 1 if no match found
                        if license_id is None:
                            license_id = 1
                            logger.warning(
                                f"Unknown license '{license_str}', defaulting to license_id=1"
                            )

                    # Map fields to ImageSchema format
                    image_data = {
                        "image_id": record.get("id"),
                        "content_type": record.get(
                            "content_type", "image/jpeg"
                        ),  # Default content type
                        "copyright_holder": record.get(
                            "copyright_holder", "Unknown"
                        ),  # Default copyright
                        "license_id": license_id,
                        "ok_for_export": bool(int(record["ok_for_export"]))
                        if "ok_for_export" in record
                        and pd.notna(record["ok_for_export"])
                        else True,
                        "diagnostic": bool(int(record["diagnostic"]))
                        if "diagnostic" in record and pd.notna(record["diagnostic"])
                        else False,
                        "width": int(record["width"])
                        if "width" in record and pd.notna(record["width"])
                        else None,
                        "height": int(record["height"])
                        if "height" in record and pd.notna(record["height"])
                        else None,
                        "rank": int(record["rank"])
                        if "rank" in record and pd.notna(record["rank"])
                        else None,
                    }

                    # Use our generic validation method instead of direct schema validation
                    validated_record = self.validate_record_against_schema(
                        image_data, "images"
                    )
                    if validated_record:
                        valid_records.append(validated_record)
                except Exception as e:
                    logger.warning(f"Error processing image record: {e}")
                    continue

            return pd.DataFrame(valid_records)

        except Exception as e:
            logger.error(f"Error processing images chunk: {e}")
            return pd.DataFrame()

    def _process_description_chunk(self, chunk: pd.DataFrame) -> pd.DataFrame:
        """Process name description data with special handling."""
        try:
            valid_records = []
            # Determine which type of description we're working with
            table_name = "name_descriptions"  # Default

            # Check if this is a location description
            if "ecology" in chunk.columns and "location_id" in chunk.columns:
                table_name = "location_descriptions"

            for _, row in chunk.iterrows():
                record = row.to_dict()

                # Handle HTML and textile markup in text fields
                for field in [
                    "gen_desc",
                    "diag_desc",
                    "distribution",
                    "habitat",
                    "look_alikes",
                    "uses",
                    "notes",
                    "refs",
                    "ecology",  # For location_descriptions
                    "species",  # For location_descriptions
                ]:
                    if field in record and pd.notna(record[field]):
                        # Process HTML and textile markup
                        text = str(record[field])
                        # Clean the text using our helper method
                        record[field] = self._clean_text(text)

                # Normalize source_type to an integer
                if "source_type" in record:
                    try:
                        record["source_type"] = int(record["source_type"])
                    except (ValueError, TypeError):
                        record["source_type"] = 0  # Default to system source (0)

                # Convert boolean fields
                for bool_field in ["public", "ok_for_export"]:
                    if bool_field in record and pd.notna(record[bool_field]):
                        record[bool_field] = str(record[bool_field]).lower() in [
                            "true",
                            "1",
                            "t",
                            "yes",
                        ]

                # Validate the record against the appropriate schema
                validated_record = self.validate_record_against_schema(
                    record, table_name
                )
                if validated_record:
                    valid_records.append(validated_record)

            return pd.DataFrame(valid_records) if valid_records else pd.DataFrame()

        except Exception as e:
            logger.error(f"Error processing description chunk: {e}")
            return pd.DataFrame()

    def _process_newline_delimited_chunk(self, chunk: pd.DataFrame) -> pd.DataFrame:
        """Process newline-delimited format files."""
        try:
            valid_records = []
            current_record = {}

            for _, row in chunk.iterrows():
                record = (
                    row.iloc[0] if len(row) > 0 else None
                )  # Get the full line as a single string

                # Skip empty lines
                if pd.isna(record) or not record.strip():
                    # Empty line means a new record boundary
                    if current_record and any(
                        k in current_record for k in ["id", "name_id", "location_id"]
                    ):
                        valid_records.append(current_record)
                        current_record = {}
                    continue

                # Check if this is a field name line
                if ":" in record:
                    field_name, value = record.split(":", 1)
                    field_name = field_name.strip().lower()
                    value = value.strip()

                    # Clean up the value
                    if value:
                        # Strip HTML
                        value = re.sub(r"<[^>]+>", "", value)
                        # Normalize whitespace
                        value = " ".join(value.split())
                        # Handle special fields
                        if field_name in ["id", "name_id", "location_id", "license_id"]:
                            try:
                                value = int(value)
                            except ValueError:
                                continue
                        elif field_name == "source_type":
                            try:
                                value = int(value)
                            except ValueError:
                                value = 0  # Default to system source
                        elif field_name in ["public", "ok_for_export"]:
                            value = value.lower() in ["true", "1", "t", "yes"]

                    # If this is a new record ID, save the previous record if any
                    if (
                        field_name in ["id", "name_id", "location_id"]
                        and current_record
                        and any(
                            k in current_record
                            for k in ["id", "name_id", "location_id"]
                        )
                    ):
                        valid_records.append(current_record)
                        current_record = {}

                    # Store field in current record
                    current_record[field_name] = value

            # Add the last record if exists
            if current_record and any(
                k in current_record for k in ["id", "name_id", "location_id"]
            ):
                valid_records.append(current_record)

            return pd.DataFrame(valid_records)

        except Exception as e:
            logger.error(f"Error processing newline-delimited chunk: {e}")
            return pd.DataFrame()

    def _manual_parse_tsv(self, file_path: Path) -> Iterator[pd.DataFrame]:
        """Manual parsing of tab-separated files as a last resort."""
        try:
            # Read file line by line
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()

            if not lines:
                yield pd.DataFrame()
                return

            # Parse header
            header = [h.strip() for h in lines[0].split("\t")]

            # Parse data rows
            data = []
            for i, line in enumerate(lines[1:], 1):
                try:
                    fields = line.split("\t")
                    # If we have extra fields, combine them into the last valid field
                    if len(fields) > len(header):
                        fields = fields[: len(header) - 1] + [
                            "\t".join(fields[len(header) - 1 :])
                        ]
                    # If we have too few fields, add None values
                    elif len(fields) < len(header):
                        fields = fields + [None] * (len(header) - len(fields))

                    # Clean up each field
                    row = {}
                    for j, field in enumerate(fields):
                        if j < len(header):
                            if field is None:
                                row[header[j]] = None
                            else:
                                field = field.strip()
                                # Convert NULL to None
                                if field.upper() == "NULL":
                                    row[header[j]] = None
                                else:
                                    row[header[j]] = field

                    data.append(row)
                except Exception as e:
                    logger.warning(f"Error parsing line {i + 1} in {file_path}: {e}")
                    continue

            # Convert to DataFrame and yield in chunks
            if data:
                df = pd.DataFrame(data)
                chunk_size = 1000
                for i in range(0, len(df), chunk_size):
                    yield df.iloc[i : i + chunk_size]
            else:
                yield pd.DataFrame()

        except Exception as e:
            logger.error(f"Error manually parsing TSV file {file_path}: {e}")
            yield pd.DataFrame()

    def _clean_text(self, text: Optional[str]) -> Optional[str]:
        """Clean text fields with special handling for HTML and textile markup."""
        if pd.isna(text) or not text:
            return None

        # Convert to string if not already
        text = str(text).strip()

        # Remove HTML tags (more comprehensive implementation)
        text = re.sub(r"<[^>]+>", "", text)

        # Process textile markup like "http://example.com":http://example.com
        # Convert to Markdown format: [text](url)
        text = re.sub(r'"([^"]+)":([^ \t\n\r\f\v]+)', r"[\1](\2)", text)

        # Handle other textile formatting
        text = re.sub(r"_(.*?)_", r"*\1*", text)  # emphasis
        text = re.sub(r"\*(.*?)\*", r"**\1**", text)  # strong

        # Preserve paragraph breaks while normalizing whitespace
        # Split by multiple newlines which indicate paragraph breaks
        paragraphs = re.split(r"\n\n+", text)
        # Normalize whitespace within each paragraph
        paragraphs = [" ".join(p.split()) for p in paragraphs]

        # Rejoin with double newlines to maintain paragraph structure
        text = "\n\n".join(paragraphs)

        # Convert special characters
        text = text.replace("―", "--")  # Convert em dash to double hyphen
        text = text.replace("…", "...")  # Convert ellipsis

        # Handle image tags
        text = re.sub(r"!image (\d+)/([^!]+)!", r"[Image: \2]", text)

        return text or None

    def _standardize_classifications(self, records: List[Dict]) -> List[Dict]:
        """Standardize taxonomy classifications."""
        standardized = []
        for record in records:
            # Remove empty values
            record = {k: v for k, v in record.items() if pd.notna(v) and v != ""}

            # Rename "class" field to "class_name" to match schema
            if "class" in record:
                record["class_name"] = record["class"]
                del record["class"]

            # Filter to include only "Fungi" kingdom entries for a mushroom field guide
            if "kingdom" in record and record["kingdom"] != "Fungi":
                logger.debug(f"Skipping non-fungi record: {record.get('name_id')}")
                continue

            # Calculate taxonomic completeness
            possible_ranks = [
                "domain",
                "kingdom",
                "phylum",
                "class_name",  # Changed from "class" to "class_name"
                "order",
                "family",
                "genus",
            ]
            present_ranks = sum(
                1 for rank in possible_ranks if rank in record and record[rank]
            )
            record["taxonomic_completeness"] = present_ranks / len(possible_ranks)

            # Try to infer genus from family if missing
            if "family" in record and "genus" not in record:
                genus = self._extract_genus_from_family(record["family"])
                if genus:
                    record["genus"] = genus

            # Standardize case for taxonomic classifications
            for rank in possible_ranks:
                if rank in record and isinstance(record[rank], str):
                    record[rank] = record[rank].capitalize()

            standardized.append(record)
        return standardized

    def _clean_value(self, value: Any) -> Any:
        """Clean numeric or boolean values."""
        if pd.isna(value):
            return None

        if isinstance(value, (int, float)):
            return value

        if isinstance(value, str):
            # Handle boolean strings
            if value.lower() in ("true", "1", "t", "yes"):
                return True
            if value.lower() in ("false", "0", "f", "no"):
                return False

            # Handle NULL values
            if value.upper() in ("NULL", "NA", "N/A", "NONE"):
                return None

            # Try to convert to number
            try:
                if "." in value:
                    return float(value)
                return int(value)
            except ValueError:
                pass

        return value

    def _extract_genus_from_family(self, family: Optional[str]) -> Optional[str]:
        """Extract genus name from family name if possible."""
        if not family:
            return None

        # Common suffixes for family names
        family_suffixes = ["aceae", "idae"]

        # Remove family suffix if present
        for suffix in family_suffixes:
            if family.lower().endswith(suffix):
                base = family[: -len(suffix)]
                # Return capitalized base as genus
                return base.capitalize()

        return None

    def validate_csv_structure(
        self, df: pd.DataFrame, expected_columns: List[str]
    ) -> bool:
        """Validate CSV file structure."""
        missing_columns = set(expected_columns) - set(df.columns)
        if missing_columns:
            self.errors.append(f"Missing required columns: {missing_columns}")
            return False
        return True

    def validate_record_against_schema(
        self, record: Dict[str, Any], table_name: str
    ) -> Optional[Dict[str, Any]]:
        """Validate a record against its corresponding schema.

        Args:
            record: The data dictionary to validate
            table_name: The name of the table/schema to validate against

        Returns:
            The validated record or None if validation fails
        """
        try:
            # Get the appropriate schema based on the table name
            schema_class = self.schema_mapping.get(table_name)
            if not schema_class:
                logger.warning(f"No schema defined for table: {table_name}")
                return record  # Return without validation if no schema exists

            # Standardize the record for schema validation
            standardized_record = self.standardize_record_for_schema(
                record, schema_class
            )

            # Use the validate_record function from schemas.py
            validated = validate_record(standardized_record, schema_class)
            return validated.model_dump()

        except ValidationError as e:
            logger.warning(f"Validation error for {table_name} record: {e}")
            if (
                hasattr(self.config, "STRICT_VALIDATION")
                and self.config.STRICT_VALIDATION
            ):
                # In strict mode, return None for invalid records
                return None
            else:
                # In relaxed mode, return original record but log the error
                self.errors.append(f"Validation error in {table_name}: {e}")
                return record
        except Exception as e:
            logger.error(f"Error validating {table_name} record: {e}")
            return record  # Return original record on unexpected errors

    def standardize_record_for_schema(
        self, record: Dict[str, Any], schema_class: Type[T]
    ) -> Dict[str, Any]:
        """Standardize a record's field types based on schema type hints before validation.

        Args:
            record: The record to standardize
            schema_class: The Pydantic schema class to use for type information

        Returns:
            A record with fields standardized according to schema types
        """
        try:
            # Get schema fields and their types
            schema_fields = schema_class.model_fields
            standardized_record = {}

            # Process each field in the record
            for field_name, value in record.items():
                # Skip empty values
                if pd.isna(value) or value == "":
                    continue

                # Get schema field info if available
                if field_name in schema_fields:
                    field_info = schema_fields[field_name]
                    annotation = field_info.annotation

                    # Convert value based on schema type annotation
                    if annotation == int or str(annotation).endswith("int"):
                        try:
                            if pd.notna(value) and value != "":
                                standardized_record[field_name] = int(float(value))
                        except (ValueError, TypeError):
                            logger.debug(
                                f"Could not convert {field_name} value '{value}' to int"
                            )

                    elif annotation == float or str(annotation).endswith("float"):
                        try:
                            if pd.notna(value) and value != "":
                                standardized_record[field_name] = float(value)
                        except (ValueError, TypeError):
                            logger.debug(
                                f"Could not convert {field_name} value '{value}' to float"
                            )

                    elif annotation == bool or str(annotation).endswith("bool"):
                        if isinstance(value, str):
                            standardized_record[field_name] = value.lower() in (
                                "true",
                                "t",
                                "1",
                                "yes",
                                "y",
                            )
                        else:
                            standardized_record[field_name] = bool(value)

                    elif annotation == str or str(annotation).endswith("str"):
                        if not isinstance(value, str):
                            standardized_record[field_name] = str(value)
                        else:
                            standardized_record[field_name] = value

                    else:
                        # For other types, keep as is
                        standardized_record[field_name] = value
                else:
                    # Field not in schema, keep as is
                    standardized_record[field_name] = value

            # Add any fields from record that weren't standardized
            for field_name, value in record.items():
                if field_name not in standardized_record and pd.notna(value):
                    standardized_record[field_name] = value

            return standardized_record

        except Exception as e:
            logger.error(f"Error standardizing record: {e}")
            # Return original record if standardization fails
            return record

    def validate_dataframe(self, df: pd.DataFrame, table_name: str) -> pd.DataFrame:
        """Validate an entire DataFrame against a schema.

        This method processes each record in the DataFrame and validates it against
        the appropriate schema, returning only records that pass validation.

        Args:
            df: The DataFrame to validate
            table_name: Name of the table/schema to validate against

        Returns:
            DataFrame containing only valid records
        """
        if table_name not in self.schema_mapping:
            logger.warning(f"No schema defined for table: {table_name}")
            return df

        schema_class = self.schema_mapping[table_name]
        valid_records = []
        invalid_count = 0

        # Process each record in the DataFrame
        for _, row in df.iterrows():
            record = row.to_dict()

            # Standardize the record for the schema
            standardized_record = self.standardize_record_for_schema(
                record, schema_class
            )

            try:
                # Validate against the schema
                validated = validate_record(standardized_record, schema_class)
                valid_records.append(validated.model_dump())
            except ValidationError as e:
                invalid_count += 1
                error_msg = str(e).replace("\n", " ")
                logger.debug(f"Validation error for {table_name} record: {error_msg}")

                # In non-strict mode, include the original record
                if (
                    not hasattr(self.config, "STRICT_VALIDATION")
                    or not self.config.STRICT_VALIDATION
                ):
                    valid_records.append(record)

        # Log validation summary
        if invalid_count > 0:
            logger.warning(
                f"Validation completed for {table_name}: {invalid_count} records failed validation"
            )
            if (
                hasattr(self.config, "STRICT_VALIDATION")
                and self.config.STRICT_VALIDATION
            ):
                logger.warning(
                    f"Strict validation mode: {invalid_count} invalid records removed"
                )
            else:
                logger.warning(
                    f"Non-strict validation mode: {invalid_count} invalid records retained with warnings"
                )

        return pd.DataFrame(valid_records) if valid_records else pd.DataFrame()

    def batch_validate(
        self, records: List[Dict[str, Any]], table_name: str, strict: bool = None
    ) -> List[Dict[str, Any]]:
        """Validate multiple records in batch mode with performance optimizations.

        Args:
            records: List of data dictionaries to validate
            table_name: Name of the table/schema to validate against
            strict: Override config STRICT_VALIDATION setting if provided

        Returns:
            List of validated records (or original records in non-strict mode)
        """
        if table_name not in self.schema_mapping:
            logger.warning(f"No schema defined for table: {table_name}")
            return records

        # Determine strictness mode
        strict_mode = (
            strict
            if strict is not None
            else (
                hasattr(self.config, "STRICT_VALIDATION")
                and self.config.STRICT_VALIDATION
            )
        )

        schema_class = self.schema_mapping[table_name]
        valid_records = []
        invalid_count = 0

        # Pre-fetch schema field info to avoid repeated lookups
        schema_fields = schema_class.model_fields

        # Process records in batch
        for record in records:
            # Skip empty records
            if not record:
                continue

            try:
                # Standardize and validate
                standardized = {
                    field_name: self._convert_value_for_field(
                        value, field_name, schema_fields
                    )
                    for field_name, value in record.items()
                    if not pd.isna(value) and value != ""
                }

                # Validate with schema
                validated = validate_record(standardized, schema_class)
                valid_records.append(validated.model_dump())

            except ValidationError as e:
                invalid_count += 1
                # Include detailed error information in debug logs
                error_msg = str(e).replace("\n", " ")
                logger.debug(f"Validation error for {table_name} record: {error_msg}")

                # In non-strict mode, keep the original record
                if not strict_mode:
                    valid_records.append(record)

        # Log validation summary
        total = len(records)
        valid = len(valid_records)

        if invalid_count > 0:
            logger.info(
                f"Batch validation summary for {table_name}: "
                f"{valid}/{total} records valid ({invalid_count} invalid)"
            )

        return valid_records

    def _convert_value_for_field(
        self, value: Any, field_name: str, schema_fields: Dict
    ) -> Any:
        """Convert a value to the appropriate type based on schema field definition.

        Args:
            value: The value to convert
            field_name: Name of the field in the schema
            schema_fields: Dictionary of schema fields

        Returns:
            Converted value
        """
        # Return None for empty values
        if pd.isna(value) or value == "":
            return None

        # If field isn't in schema, return as is
        if field_name not in schema_fields:
            return value

        field_info = schema_fields[field_name]
        annotation = field_info.annotation

        # Convert based on schema type annotation
        try:
            if annotation == int or str(annotation).endswith("int"):
                if pd.notna(value) and value != "":
                    return int(float(value))

            elif annotation == float or str(annotation).endswith("float"):
                if pd.notna(value) and value != "":
                    return float(value)

            elif annotation == bool or str(annotation).endswith("bool"):
                if isinstance(value, str):
                    return value.lower() in ("true", "t", "1", "yes", "y")
                return bool(value)

            elif annotation == str or str(annotation).endswith("str"):
                if not isinstance(value, str):
                    return str(value)
                return value
        except (ValueError, TypeError):
            # If conversion fails, return original value
            logger.debug(f"Could not convert {field_name}={value} to {annotation}")

        return value

    def bulk_update_from_schema(
        self, records: List[Dict[str, Any]], table_name: str
    ) -> List[Dict[str, Any]]:
        """Update records with default values from schema fields when values are missing.

        This is useful for filling in default values defined in the schema model.

        Args:
            records: List of records to update
            table_name: Name of the schema to use

        Returns:
            Updated list of records with defaults applied
        """
        if table_name not in self.schema_mapping:
            return records

        schema_class = self.schema_mapping[table_name]
        schema_fields = schema_class.model_fields
        updated_records = []

        for record in records:
            # Skip empty records
            if not record:
                continue

            updated_record = record.copy()

            # Apply defaults from schema for missing fields
            for field_name, field_info in schema_fields.items():
                if field_name not in updated_record or pd.isna(
                    updated_record[field_name]
                ):
                    # Check if field has a default value in the schema
                    if field_info.default is not None and field_info.default is not ...:
                        updated_record[field_name] = field_info.default

                    # If no default but the field has a default factory, use it
                    elif (
                        hasattr(field_info, "default_factory")
                        and field_info.default_factory is not None
                    ):
                        try:
                            updated_record[field_name] = field_info.default_factory()
                        except Exception as e:
                            logger.debug(
                                f"Could not use default_factory for {field_name}: {e}"
                            )

            updated_records.append(updated_record)

        return updated_records

    def analyze_schema_conformity(
        self, df: pd.DataFrame, table_name: str
    ) -> Dict[str, Any]:
        """Analyze how well a DataFrame conforms to its schema constraints.

        This is useful for data quality reporting and identifying problematic fields.

        Args:
            df: The DataFrame to analyze
            table_name: Name of the schema to check against

        Returns:
            Dict with analysis results including field-level statistics
        """
        if table_name not in self.schema_mapping:
            return {"error": f"No schema defined for table: {table_name}"}

        schema_class = self.schema_mapping[table_name]
        schema_fields = schema_class.model_fields
        total_records = len(df)
        result = {
            "table": table_name,
            "total_records": total_records,
            "fields": {},
            "overall_conformity": 0.0,
            "potential_issues": [],
        }

        # Skip analysis if DataFrame is empty
        if total_records == 0:
            return result

        field_conformity_scores = []

        # Analyze each field in the schema
        for field_name, field_info in schema_fields.items():
            field_stats = {
                "present": field_name in df.columns,
                "null_count": 0,
                "type_mismatch_count": 0,
                "conformity_score": 0.0,
                "constraint_violations": 0,
            }

            # Skip analysis if field is not in DataFrame
            if not field_stats["present"]:
                field_stats["error"] = f"Field '{field_name}' not present in DataFrame"
                result["fields"][field_name] = field_stats
                field_conformity_scores.append(0.0)
                result["potential_issues"].append(f"Missing field: {field_name}")
                continue

            # Count null values
            field_stats["null_count"] = df[field_name].isna().sum()
            field_stats["null_percentage"] = (
                field_stats["null_count"] / total_records
            ) * 100

            # Get field type information
            annotation = field_info.annotation
            expected_type = None

            if annotation == int or str(annotation).endswith("int"):
                expected_type = "int"
            elif annotation == float or str(annotation).endswith("float"):
                expected_type = "float"
            elif annotation == bool or str(annotation).endswith("bool"):
                expected_type = "bool"
            elif annotation == str or str(annotation).endswith("str"):
                expected_type = "str"
            else:
                expected_type = str(annotation)

            field_stats["expected_type"] = expected_type

            # Check for type mismatches
            type_mismatches = 0
            constraint_violations = 0

            # Create a temporary series with non-null values converted to expected type for constraint checking
            non_null_values = df[field_name].dropna()

            for value in non_null_values:
                # Check type conformance
                if expected_type == "int":
                    try:
                        int(float(value))
                    except (ValueError, TypeError):
                        type_mismatches += 1

                elif expected_type == "float":
                    try:
                        float(value)
                    except (ValueError, TypeError):
                        type_mismatches += 1

                elif expected_type == "bool" and not isinstance(value, bool):
                    if isinstance(value, str) and value.lower() not in (
                        "true",
                        "false",
                        "1",
                        "0",
                        "t",
                        "f",
                        "yes",
                        "no",
                        "y",
                        "n",
                    ):
                        type_mismatches += 1
                    elif not isinstance(value, (int, float)):
                        type_mismatches += 1

                elif expected_type == "str" and not isinstance(value, str):
                    # Most values can be converted to string, so we don't count this as a mismatch
                    pass

            field_stats["type_mismatch_count"] = type_mismatches
            field_stats["type_mismatch_percentage"] = (
                type_mismatches / total_records
            ) * 100

            # Calculate field conformity score (100% - issues%)
            issues_percentage = (
                (field_stats["null_count"] + type_mismatches) / total_records * 100
            )
            field_stats["conformity_score"] = 100.0 - issues_percentage
            field_conformity_scores.append(field_stats["conformity_score"])

            # Add field to result
            result["fields"][field_name] = field_stats

            # Log potential issues
            if (
                field_stats["null_count"] > 0
                and hasattr(field_info, "required")
                and field_info.required
            ):
                result["potential_issues"].append(
                    f"Required field '{field_name}' has {field_stats['null_count']} null values"
                )

            if type_mismatches > 0:
                result["potential_issues"].append(
                    f"Field '{field_name}' has {type_mismatches} type mismatches"
                )

        # Calculate overall conformity score (average of field scores)
        if field_conformity_scores:
            result["overall_conformity"] = sum(field_conformity_scores) / len(
                field_conformity_scores
            )

        return result
