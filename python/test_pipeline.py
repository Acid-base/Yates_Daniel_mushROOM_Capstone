"""Test the CSV processor and pipeline components individually."""

import sys
import time
import asyncio
from pathlib import Path

# Import all necessary components
from src.config import load_config, DataConfig
from src.data_csv import CSVProcessor
from src.log_utils import get_logger
from src.database import AsyncDatabase
from src.schemas import validate_record, NameSchema, SpeciesSchema

logger = get_logger(__name__)


# Set up component tests
class ComponentTester:
    """Test individual components of the pipeline."""

    def __init__(self, config: DataConfig):
        """Initialize with config."""
        self.config = config
        self.csv_processor = CSVProcessor(config)
        self.db = None
        self.test_results = {}

    async def setup_db(self):
        """Test database connection."""
        print("\n=== Testing Database Connection ===")
        try:
            self.db = AsyncDatabase(self.config)
            await self.db.connect()
            print("✅ Database connection successful")
            self.test_results["database_connection"] = True

            # Test indexes creation
            try:
                await self.db.ensure_names_indexes()
                print("✅ Names indexes created successfully")
                self.test_results["names_indexes"] = True

                await self.db.ensure_species_indexes()
                print("✅ Species indexes created successfully")
                self.test_results["species_indexes"] = True
            except Exception as e:
                print(f"❌ Error creating indexes: {e}")
                self.test_results["indexes_creation"] = False

            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            self.test_results["database_connection"] = False
            return False

    async def cleanup_db(self):
        """Close database connection."""
        if self.db:
            await self.db.close()
            print("Database connection closed")

    def test_validation(self):
        """Test pydantic validation."""
        print("\n=== Testing Schema Validation ===")
        try:
            # Test name schema
            test_name = {
                "id": 1,
                "text_name": "Amanita muscaria",
                "display_name": "Amanita muscaria",
                "search_name": "amanita muscaria",
                "sort_name": "Amanita muscaria",
                "author": "L.",
                "rank": 4,
                "deprecated": False,
            }
            valid_name = validate_record(test_name, NameSchema)
            print("✅ Name schema validation successful")

            # Test species schema
            test_species = {
                "_id": 1,
                "scientific_name": "Amanita muscaria",
                "author": "L.",
                "rank": 4,
                "deprecated": False,
                "synonyms": [],
                "is_group": False,
            }
            valid_species = validate_record(test_species, SpeciesSchema)
            print("✅ Species schema validation successful")

            self.test_results["schema_validation"] = True
            return True
        except Exception as e:
            print(f"❌ Schema validation failed: {e}")
            self.test_results["schema_validation"] = False
            return False

    def test_csv_reading(self, filename="names.csv"):
        """Test reading a single CSV file."""
        print(f"\n=== Testing CSV Reading: {filename} ===")
        try:
            file_path = Path(self.config.DATA_DIR) / filename

            if not file_path.exists():
                print(f"❌ File not found: {file_path}")
                self.test_results[f"csv_reading_{filename}"] = False
                return False

            print(f"File exists: {file_path}")
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            print(f"File size: {file_size_mb:.2f} MB")

            # Set processor options based on file type
            processor_options = self._get_processor_options(filename)
            print(f"Using processor options: {processor_options}")

            start_time = time.time()
            record_count = 0
            chunk_count = 0

            print("Reading file in chunks...")
            for records_batch in self.csv_processor.read_chunks(
                file_path, **processor_options
            ):
                chunk_count += 1

                if records_batch is not None and not records_batch.empty:
                    batch_size = len(records_batch)
                    record_count += batch_size

                    # Show progress
                    if chunk_count == 1:
                        print(f"First chunk columns: {list(records_batch.columns)}")
                        print(f"Sample data:\n{records_batch.head(2)}")

                    if chunk_count % 10 == 0:
                        elapsed = time.time() - start_time
                        print(
                            f"Progress: {chunk_count} chunks, {record_count} records in {elapsed:.2f} seconds"
                        )
                        sys.stdout.flush()  # Force output to show immediately

            elapsed = time.time() - start_time
            print(
                f"✅ Successfully read {filename}: {record_count} records in {elapsed:.2f} seconds"
            )
            self.test_results[f"csv_reading_{filename}"] = True
            return True

        except Exception as e:
            print(f"❌ Error reading {filename}: {e}")
            import traceback

            traceback.print_exc()
            self.test_results[f"csv_reading_{filename}"] = False
            return False

    async def test_store_records(self, filename="names.csv", limit=100):
        """Test storing records in the database."""
        print(f"\n=== Testing DB Record Storage: {filename} ===")

        if not self.db:
            print("❌ Database not connected, skipping storage test")
            self.test_results["record_storage"] = False
            return False

        try:
            # Read a small batch of records
            file_path = Path(self.config.DATA_DIR) / filename
            processor_options = self._get_processor_options(filename)

            # Get collection name from filename
            collection_name = filename.split(".")[0]

            # Read and store records
            record_count = 0
            stored_count = 0

            for records_batch in self.csv_processor.read_chunks(
                file_path, **processor_options
            ):
                if records_batch is not None and not records_batch.empty:
                    # Only take a small sample for testing
                    if record_count >= limit:
                        break

                    batch_records = records_batch.head(
                        min(100, len(records_batch))
                    ).to_dict(orient="records")
                    record_count += len(batch_records)

                    # Store records
                    result = await self.db.store_records(collection_name, batch_records)
                    stored_count += result

                    print(f"Stored {result} records in {collection_name}")

                    if record_count >= limit:
                        break

            print(f"✅ Successfully stored {stored_count} records in {collection_name}")
            self.test_results["record_storage"] = True
            return True

        except Exception as e:
            print(f"❌ Error storing records: {e}")
            import traceback

            traceback.print_exc()
            self.test_results["record_storage"] = False
            return False

    def _get_processor_options(self, filename):
        """Get processor options based on filename."""
        if "names.csv" in filename:
            return {
                "sep": "\t",
                "header": 0,
                "on_bad_lines": "skip",
                "quoting": 3,  # QUOTE_NONE
            }
        elif "locations.csv" in filename:
            return {
                "sep": "\t",
                "header": 0,
                "quoting": 3,  # QUOTE_NONE
                "engine": "python",
                "on_bad_lines": "skip",
            }
        elif (
            "name_descriptions.csv" in filename
            or "location_descriptions.csv" in filename
        ):
            return {
                "header": None,
                "names": ["content"],
                "engine": "python",
                "delimiter": "\n",
            }
        else:
            return {"sep": "\t", "header": 0, "on_bad_lines": "skip"}

    def report_results(self):
        """Report all test results."""
        print("\n=== Test Results Summary ===")

        for test_name, result in self.test_results.items():
            print(f"{test_name}: {'✅ Pass' if result else '❌ Fail'}")

        # Overall result
        success = all(self.test_results.values())
        print(
            f"\nOverall Result: {'✅ All tests passed' if success else '❌ Some tests failed'}"
        )
        return success


async def main():
    """Run all component tests."""
    try:
        print("Starting component tests")

        # Setup logging
        setup_logging()

        # Load configuration
        config = load_config()

        # Create component tester
        tester = ComponentTester(config)

        # Run tests
        tester.test_validation()

        # CSV file tests - run them first without DB to check parsing
        test_files = ["names.csv"]  # Add more files as needed
        for filename in test_files:
            tester.test_csv_reading(filename)

        # Database tests
        db_connected = await tester.setup_db()
        if db_connected:
            # Only run DB storage tests if connection worked
            for filename in test_files:
                await tester.test_store_records(filename)

        # Clean up database connection
        await tester.cleanup_db()

        # Report results
        success = tester.report_results()
        return 0 if success else 1

    except Exception as e:
        print(f"Error in test script: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    # Run the async main function
    sys.exit(asyncio.run(main()))
