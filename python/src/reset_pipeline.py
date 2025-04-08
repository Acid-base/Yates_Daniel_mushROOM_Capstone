"""Utility script to reset the pipeline progress."""

import json
import argparse
from pathlib import Path
from datetime import datetime


def reset_pipeline_progress(progress_file: Path, reset_species_only: bool = False):
    """
    Reset the pipeline progress file.

    Args:
        progress_file: Path to the progress JSON file
        reset_species_only: If True, only reset species documents progress
    """
    if progress_file.exists():
        try:
            # Read existing file
            with open(progress_file, "r") as f:
                data = json.load(f)

            if reset_species_only:
                # Only reset species_documents in the processed tables
                if (
                    "csv_tables_processed" in data
                    and "species_documents" in data["csv_tables_processed"]
                ):
                    data["csv_tables_processed"].remove("species_documents")
                print(f"Reset species documents progress in {progress_file}")
            else:
                # Reset all progress
                data = {
                    "csv_tables_processed": [],
                    "api_enrichment": {},
                    "last_update": datetime.now().isoformat(),
                    "errors": [],
                    "stats": {
                        "total_records": 0,
                        "processed_records": 0,
                        "failed_records": 0,
                        "start_time": None,
                        "end_time": None,
                    },
                }
                print(f"Reset all pipeline progress in {progress_file}")

            # Write back to file
            with open(progress_file, "w") as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            print(f"Error resetting progress file: {e}")
    else:
        print(f"Progress file {progress_file} does not exist. Nothing to reset.")


def main():
    """Main function to parse arguments and reset progress."""
    parser = argparse.ArgumentParser(description="Reset mushroom pipeline progress")
    parser.add_argument(
        "--species-only",
        action="store_true",
        help="Only reset species documents progress (keep other tables)",
    )
    args = parser.parse_args()

    # Get the path to the progress file
    script_dir = Path(__file__).parent.parent  # Go up from src to python folder
    progress_file = script_dir / "pipeline_progress.json"

    reset_pipeline_progress(progress_file, args.species_only)


if __name__ == "__main__":
    main()
