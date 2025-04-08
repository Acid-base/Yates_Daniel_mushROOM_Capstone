"""
Enhanced CSV Processing Module.

This module extends the functionality of the base CSVProcessor with improved
handling of complex CSV files with embedded newlines, HTML content, and
special formatting.
"""

import csv
import io
import logging
import re
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

import pandas as pd
from data_csv import CSVProcessor

logger = logging.getLogger(__name__)


class EnhancedCSVProcessor(CSVProcessor):
    """Enhanced CSV processor with improved handling of complex CSV files."""

    def read_chunks(
        self, file_path: Path, **kwargs
    ) -> Iterator[Optional[pd.DataFrame]]:
        """
        Enhanced version of read_chunks that uses improved parsing for complex files.

        This method first attempts to use the standard CSV reading approach.
        If that fails, it tries the enhanced parsing methods.
        """
        # First try the standard approach from the parent class
        try:
            standard_reader = super().read_chunks(file_path, **kwargs)
            first_chunk = next(standard_reader, None)

            # If we successfully got a chunk, yield it and continue with standard reading
            if first_chunk is not None and not first_chunk.empty:
                yield first_chunk
                for chunk in standard_reader:
                    yield chunk
                return
        except Exception as e:
            logger.warning(f"Standard CSV reading failed: {e}")
            # Continue to enhanced methods

        # Enhanced reading methods for complex files
        file_path_str = str(file_path)
        complex_tsv = (
            "name_descriptions.csv" in file_path_str
            or "location_descriptions.csv" in file_path_str
        )

        if complex_tsv:
            logger.info(f"Using enhanced processing for complex file: {file_path}")
            yield from self.read_complex_csv_file(file_path, **kwargs)
        else:
            # For other files, try manual parsing as last resort
            logger.debug("Trying manual TSV parsing")
            yield from self._manual_parse_tsv(file_path)

    def read_complex_csv_file(
        self, file_path: Path, **kwargs
    ) -> Iterator[pd.DataFrame]:
        """
        Read complex CSV files with embedded newlines and special formatting.

        Args:
            file_path: Path to the complex CSV file
            **kwargs: Additional parameters to control the parsing

        Returns:
            Iterator of DataFrames containing the processed records
        """
        try:
            logger.info(f"Reading complex format file: {file_path}")
            file_name = file_path.name.lower()

            # Determine expected headers based on file type
            is_name_desc = "name_descriptions" in file_name
            is_location_desc = "location_descriptions" in file_name

            if not (is_name_desc or is_location_desc):
                logger.warning(
                    f"File {file_path} is not recognized as a complex format file"
                )
                yield pd.DataFrame()
                return

            # Set expected headers based on file type
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

            # Try multiple approaches to read the file
            records = []

            # 1. First try: Standard CSV reader with special quoting options
            records = self._try_standard_csv_reader(file_path)

            # 2. Second try: Special format reader if standard failed
            if not records:
                records = self._try_special_format_reader(file_path)

            # 3. Third try: Line by line processing if all else fails
            if not records:
                records = self._try_line_by_line_reader(file_path)

            # 4. Final try: Process raw file as a fallback
            if not records:
                records = self._process_name_descriptions(file_path)

            # Post-process records
            if records:
                # Clean text fields
                for record in records:
                    for field, value in record.items():
                        if isinstance(value, str):
                            record[field] = self._clean_text(value)

                # Ensure all records have the expected headers
                for record in records:
                    for header in expected_headers:
                        if header not in record:
                            record[header] = None

                # Convert ID fields to integers where possible
                for record in records:
                    for id_field in ["id", "name_id", "location_id"]:
                        if id_field in record and record[id_field]:
                            try:
                                record[id_field] = int(record[id_field])
                            except (ValueError, TypeError):
                                # If conversion fails, keep as is
                                pass

                # Convert source_type to integer
                for record in records:
                    if "source_type" in record and record["source_type"]:
                        try:
                            record["source_type"] = int(record["source_type"])
                        except (ValueError, TypeError):
                            record["source_type"] = 0  # Default to system source

                # Yield records in batches
                batch_size = kwargs.get(
                    "chunksize", self.csv_params.get("chunksize", 1000)
                )
                for i in range(0, len(records), batch_size):
                    batch = records[i : i + batch_size]
                    if batch:
                        yield pd.DataFrame(batch)
            else:
                logger.error(f"Failed to extract any records from {file_path}")
                yield pd.DataFrame()

        except Exception as e:
            logger.error(f"Error reading complex CSV file {file_path}: {e}")
            yield pd.DataFrame()

    def _try_standard_csv_reader(self, file_path: Path) -> List[Dict[str, Any]]:
        """Try to read the file using standard CSV reader with special quoting."""
        records = []
        try:
            logger.debug("Attempting to read with standard CSV reader")
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            # Process with CSV reader
            csv_reader = csv.reader(
                io.StringIO(content),
                delimiter="\t",
                quotechar='"',
                quoting=csv.QUOTE_MINIMAL,
            )

            # Get header row
            header = next(csv_reader, [])
            if not header:
                return []

            # Process data rows
            for row in csv_reader:
                if not row:
                    continue

                record = {}
                # Map values to header names
                for i, field in enumerate(row):
                    if i < len(header):
                        record[header[i]] = field

                # Add record if it has some content
                if record:
                    records.append(record)

            logger.info(
                f"Successfully read {len(records)} records with standard CSV reader"
            )
            return records
        except Exception as e:
            logger.debug(f"Standard CSV reader failed: {e}")
            return []

    def _try_special_format_reader(self, file_path: Path) -> List[Dict[str, Any]]:
        """Try to read the file using a special format reader for embedded newlines."""
        records = []
        try:
            logger.debug("Attempting to read with special format reader")
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            # Split the content into records based on blank lines
            raw_records = re.split(r"\n\s*\n+", content)

            for raw_record in raw_records:
                if not raw_record.strip():
                    continue

                record = {}
                current_field = None

                for line in raw_record.split("\n"):
                    line = line.strip()
                    if not line:
                        continue

                    # Check if line defines a field (e.g., "id: 123")
                    match = re.match(r"^([^:]+):\s*(.*?)$", line)
                    if match:
                        field_name = match.group(1).lower().strip()
                        value = match.group(2).strip()

                        # Map to standard field names
                        if field_name == "id":
                            current_field = "id"
                        elif field_name == "name_id":
                            current_field = "name_id"
                        elif field_name == "location_id":
                            current_field = "location_id"
                        elif field_name in [
                            "description",
                            "desc",
                            "general description",
                        ]:
                            current_field = "gen_desc"
                        elif field_name in ["diagnostic", "diagnostic description"]:
                            current_field = "diag_desc"
                        elif field_name == "distribution":
                            current_field = "distribution"
                        elif field_name in ["habitat", "ecology"]:
                            current_field = (
                                "habitat"
                                if "name_descriptions" in str(file_path)
                                else "ecology"
                            )
                        elif field_name in ["look alikes", "look-alikes", "lookalikes"]:
                            current_field = "look_alikes"
                        elif field_name in ["uses", "edibility"]:
                            current_field = "uses"
                        elif field_name == "notes":
                            current_field = "notes"
                        elif field_name in ["refs", "references"]:
                            current_field = "refs"
                        elif field_name == "source_type":
                            current_field = "source_type"
                        elif field_name == "source_name":
                            current_field = "source_name"
                        elif field_name == "species":
                            current_field = "species"
                        else:
                            # If we don't recognize the field, use the field name directly
                            current_field = field_name

                        # Store the value
                        record[current_field] = value
                    else:
                        # This is a continuation of the previous field
                        if current_field and current_field in record:
                            record[current_field] += "\n" + line
                        elif current_field:
                            record[current_field] = line
                        else:
                            # If we don't have a current field, use notes
                            if "notes" not in record:
                                record["notes"] = line
                            else:
                                record["notes"] += "\n" + line

                # Add record if it has some content
                if record and any(
                    k in record for k in ["id", "name_id", "location_id"]
                ):
                    records.append(record)

            logger.info(
                f"Successfully read {len(records)} records with special format reader"
            )
            return records
        except Exception as e:
            logger.debug(f"Special format reader failed: {e}")
            return []

    def _try_line_by_line_reader(self, file_path: Path) -> List[Dict[str, Any]]:
        """Read the file line by line, trying to construct records."""
        records = []
        try:
            logger.debug("Attempting to read line by line")
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()

            # Extract header line
            if not lines:
                return []

            header_line = lines[0]
            headers = [h.strip() for h in header_line.split("\t")]

            current_record = {}
            for line in lines[1:]:
                line = line.strip()
                if not line:
                    # Empty line - save current record if it exists
                    if current_record:
                        records.append(current_record)
                        current_record = {}
                    continue

                # Split the line into fields
                fields = line.split("\t")

                # Create a new record
                record = {}
                for i, field in enumerate(fields):
                    if i < len(headers):
                        record[headers[i]] = field

                # If this looks like a complete record, add it
                if record.get("id") or len(fields) == len(headers):
                    records.append(record)
                    current_record = {}
                else:
                    # This might be a continuation of the previous record
                    for i, field in enumerate(fields):
                        field = field.strip()
                        if field and i < len(headers):
                            header = headers[i]
                            if header in current_record:
                                current_record[header] += " " + field
                            else:
                                current_record[header] = field

            # Add the last record if any
            if current_record:
                records.append(current_record)

            logger.info(f"Successfully read {len(records)} records line by line")
            return records
        except Exception as e:
            logger.debug(f"Line-by-line reader failed: {e}")
            return []

    def _process_name_descriptions(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Specialized parser for name_descriptions.csv format.
        Handle the specific format found in the mushROOM project.
        """
        records = []
        record_id = 1  # Start with ID 1 if none are found

        try:
            logger.debug("Attempting to read with specialized name_descriptions parser")
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            # Split content into chunks that might be records
            chunks = re.split(r"(Invalid\s+(?:id|name_id)\s+value:[^\n]*\n)", content)

            current_record = {}
            for chunk in chunks:
                # Check if this is a marker for a new record
                if chunk.startswith("Invalid"):
                    # Save previous record if it exists
                    if current_record:
                        records.append(current_record)

                    # Start a new record
                    current_record = {
                        "id": record_id,
                        "gen_desc": "",  # Default field for content
                    }
                    record_id += 1

                    # Extract name_id or other ID if present
                    match = re.search(
                        r"Invalid\s+(name_id|id)\s+value:\s*(.*?)$", chunk
                    )
                    if match:
                        field_type = match.group(1)
                        value = match.group(2).strip()

                        if field_type == "name_id":
                            # Try to extract an ID if it's numeric
                            name_id = self._extract_or_convert_id(value)
                            if name_id:
                                current_record["name_id"] = name_id
                            else:
                                # If not numeric, store as part of the general description
                                current_record["gen_desc"] += value
                        elif field_type == "id" and value.isdigit():
                            # Use this ID if it's a valid number
                            current_record["id"] = int(value)
                else:
                    # This is content for the current record
                    if current_record:
                        if "gen_desc" in current_record:
                            current_record["gen_desc"] += " " + chunk.strip()
                        else:
                            current_record["gen_desc"] = chunk.strip()

            # Add the last record
            if current_record:
                records.append(current_record)

            logger.info(
                f"Successfully read {len(records)} records with specialized parser"
            )
            return records
        except Exception as e:
            logger.debug(f"Specialized parser failed: {e}")
            return []

    def _extract_or_convert_id(self, text: str) -> Optional[int]:
        """
        Extract valid numeric ID from the text or return None.
        Handles cases like 'http://website.com' where text is not an actual ID.
        """
        if not text:
            return None

        # Check if the text is a URL - not a valid ID
        if "http://" in text or "https://" in text or "www." in text:
            return None

        # Try to extract a numeric ID
        match = re.search(r"\b\d+\b", text)
        if match:
            try:
                return int(match.group(0))
            except ValueError:
                return None
        return None

    def _clean_text(self, text: Optional[str]) -> Optional[str]:
        """Clean text fields with special handling for HTML and textile markup."""
        if pd.isna(text) or not text:
            return None

        # Convert to string if not already
        text = str(text).strip()

        # Remove HTML tags
        text = re.sub(r"<[^>]+>", "", text)

        # Process textile markup like "http://example.com":http://example.com
        # Convert to Markdown format: [text](url)
        text = re.sub(r'"([^"]+)":([^ \t\n\r\f\v]+)', r"[\1](\2)", text)

        # Replace escaped newlines with spaces
        text = text.replace("\\n", " ")

        # Normalize whitespace while preserving paragraph structure
        paragraphs = re.split(r"\n\n+", text)
        paragraphs = [" ".join(p.split()) for p in paragraphs]
        text = "\n\n".join(paragraphs)

        return text or None
