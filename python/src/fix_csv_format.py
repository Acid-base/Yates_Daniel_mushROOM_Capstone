#!/usr/bin/env python
"""
Script to fix CSV format issues in name_descriptions.csv and other complex CSV files.

This script addresses the specific issues with parsing certain complex CSV files
in the mushROOM project, particularly name_descriptions.csv which has embedded
newlines, HTML, textile markup, and improper escaping.

Usage:
  python fix_csv_format.py [--input INPUT_FILE] [--output OUTPUT_FILE]
"""

import argparse
import csv
import re
from pathlib import Path


def clean_text(text):
    """Clean text fields with special handling for HTML and textile markup."""
    if text is None or not text:
        return ""

    # Convert to string if not already
    text = str(text).strip()

    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)

    # Process textile markup like "http://example.com":http://example.com
    # Convert to Markdown format: [text](url)
    text = re.sub(r'"([^"]+)":([^ \t\n\r\f\v]+)', r"[\1](\2)", text)

    # Replace escaped newlines with spaces
    text = text.replace("\\n", " ")

    # Normalize whitespace
    text = " ".join(text.split())

    return text


def extract_or_convert_id(text):
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


def fix_csv_file(input_file, output_file, delimiter="\t"):
    """Fix CSV format issues in the input file and write to output file."""
    print(f"Processing {input_file} -> {output_file}")

    # Ensure the output directory exists
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Try to read as a standard CSV first
        records = read_standard_csv(input_file, delimiter)
        if records and len(records) > 0:
            print(f"Successfully read {len(records)} records from standard CSV format")
        else:
            # If that fails, read as a special format
            records = read_special_format(input_file)
            print(f"Read {len(records)} records from special format")
    except Exception as e:
        print(f"Error reading file: {e}")
        print("Falling back to line-by-line processing...")
        records = read_line_by_line(input_file)

    # No records found - final fallback to handle name_descriptions.csv specifically
    if not records:
        print(
            "No records found. Using specialized parser for name_descriptions format..."
        )
        records = process_name_descriptions(input_file)

    # If we still have no records, we can't proceed
    if not records:
        print("WARNING: No records could be extracted from the file.")
        return 0

    # Get field names from records
    fieldnames = set()
    for record in records:
        fieldnames.update(record.keys())
    fieldnames = sorted(list(fieldnames))

    # Ensure required fields are present
    if "id" not in fieldnames:
        fieldnames.insert(0, "id")
    if "name_id" not in fieldnames and "name_descriptions" in input_file.lower():
        fieldnames.insert(1, "name_id")

    # Write the fixed CSV to output file
    with open(output_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
            delimiter=delimiter,
            quoting=csv.QUOTE_MINIMAL,
            quotechar='"',
        )
        writer.writeheader()

        for record in records:
            # Ensure all fields are present
            for header in fieldnames:
                if header not in record:
                    record[header] = ""

            # Write the record
            writer.writerow(record)

    print(f"Processed {len(records)} records. Output written to {output_file}")
    return len(records)


def read_standard_csv(input_file, delimiter="\t"):
    """Try to read the file as a standard CSV."""
    records = []
    try:
        with open(input_file, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            for row in reader:
                records.append({k: clean_text(v) for k, v in row.items()})
        return records
    except Exception as e:
        print(f"Standard CSV read failed: {e}")
        return []


def read_special_format(input_file):
    """Read file as a special format with embedded newlines."""
    records = []
    try:
        with open(input_file, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        # Split the content into records based on blank lines
        raw_records = re.split(r"\n\s*\n+", content)

        for raw_record in raw_records:
            if not raw_record.strip():
                continue

            record = {}
            current_field = "notes"  # Default field if no fields are specified

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
                    elif field_name == "description" or field_name == "gen_desc":
                        current_field = "gen_desc"
                    elif field_name == "diagnostic" or field_name == "diag_desc":
                        current_field = "diag_desc"
                    else:
                        # Use the field name as-is
                        current_field = field_name

                    # Store the value
                    record[current_field] = value
                else:
                    # This is a continuation of the previous field
                    if current_field in record:
                        record[current_field] += " " + line
                    else:
                        record[current_field] = line

            # Clean up and add the record if it has some content
            if record:
                # Clean all text fields
                record = {k: clean_text(v) for k, v in record.items()}
                records.append(record)

        return records
    except Exception as e:
        print(f"Special format read failed: {e}")
        return []


def read_line_by_line(input_file):
    """Process the file line by line, trying to construct records."""
    records = []
    try:
        with open(input_file, "r", encoding="utf-8", errors="replace") as f:
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
                    record[headers[i]] = clean_text(field)

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
                            current_record[header] += " " + clean_text(field)
                        else:
                            current_record[header] = clean_text(field)

        # Add the last record if any
        if current_record:
            records.append(current_record)

        return records
    except Exception as e:
        print(f"Line-by-line read failed: {e}")
        return []


def process_name_descriptions(input_file):
    """
    Specialized parser for name_descriptions.csv format.
    Handle the specific format found in the mushROOM project.
    """
    records = []
    record_id = 1  # Start with ID 1 if none are found

    try:
        with open(input_file, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        # Split content into chunks that might be records
        # Look for patterns like "Invalid id value:" or "Invalid name_id value:" in the logs
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
                match = re.search(r"Invalid\s+(name_id|id)\s+value:\s*(.*?)$", chunk)
                if match:
                    field_type = match.group(1)
                    value = match.group(2).strip()

                    if field_type == "name_id":
                        # Try to extract an ID if it's numeric
                        name_id = extract_or_convert_id(value)
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

        # Clean up all records
        for record in records:
            for key in record:
                if isinstance(record[key], str):
                    record[key] = clean_text(record[key])

        return records
    except Exception as e:
        print(f"Name descriptions parser failed: {e}")
        return []


def main():
    """Main function to run the script."""
    parser = argparse.ArgumentParser(
        description="Fix CSV format issues in complex CSV files."
    )
    parser.add_argument(
        "--input",
        type=str,
        default="data/name_descriptions.csv",
        help="Path to input CSV file",
    )
    parser.add_argument(
        "--output", type=str, default=None, help="Path to output fixed CSV file"
    )

    args = parser.parse_args()

    # If output is not specified, create a backup in the same directory
    input_path = Path(args.input)
    if not args.output:
        output_path = input_path.with_name(
            f"{input_path.stem}_fixed{input_path.suffix}"
        )
        args.output = str(output_path)

    # Process the file
    count = fix_csv_file(args.input, args.output)
    print(f"Successfully processed {count} records")


if __name__ == "__main__":
    main()
