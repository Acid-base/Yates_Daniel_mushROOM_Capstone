"""Tests for data pipeline utility functions and monitoring."""

import pytest
import asyncio
from datetime import datetime

from src.monitoring import measure_performance
from src.data_pipeline import DataPipeline
from src.config import DataConfig

# Import utility functions from your data_csv.py (replace with your actual import)
from src.data_csv import (
    safe_cast,
    clean_text,
    parse_date,
    validate_taxonomy,
    determine_location_type,
    parse_location_hierarchy,
)


@pytest.fixture
def utility_config():
    """Create test configuration for utility function tests."""
    return DataConfig(
        MONGODB_URI="mongodb://localhost:27017",
        DATABASE_NAME="test_mushroom_utils",
        BATCH_SIZE=100,
        NULL_VALUES=("", "NA", "N/A", "NULL", "NaN", "None"),
    )


class TestUtilityFunctions:
    @pytest.mark.parametrize(
        "input_value, type_cast, expected",
        [
            ("123", int, 123),
            ("12.34", float, 12.34),
            ("NULL", int, None),
            ("", float, None),
            ("invalid", int, "invalid"),
            ("invalid", float, None),
        ],
    )
    def test_safe_cast(self, input_value, type_cast, expected):
        """Test the safe_cast utility function."""
        assert safe_cast(input_value, type_cast) == expected

    @pytest.mark.parametrize(
        "input_text, expected",
        [
            ("<p>Test</p>", "Test"),
            ('"Link":http://example.com', "Link (http://example.com)"),
            ("  Test  \n\n  Text  ", "Test  \n  Text"),
            ("NULL", None),
            (None, None),
        ],
    )
    def test_clean_text(self, input_text, expected):
        """Test the clean_text utility function."""
        assert clean_text(input_text) == expected

    @pytest.mark.parametrize(
        "date_string, expected",
        [
            ("2023-01-01", datetime(2023, 1, 1)),
            ("invalid", None),
            ("", None),
            (None, None),
        ],
    )
    def test_parse_date(self, date_string, expected):
        """Test the parse_date utility function."""
        assert parse_date(date_string) == expected

    @pytest.mark.parametrize(
        "taxonomy_data, expected_error",
        [
            ({}, "Missing required taxonomic ranks"),
            ({"domain": "Eukarya"}, "Missing required taxonomic ranks"),
            (
                {
                    "domain": "Eukarya",
                    "kingdom": "Fungi",
                    "phylum": "Ascomycota",
                    "class": "Lecanoromycetes",
                    "order": "Lecanorales",
                    "family": "Parmeliaceae",
                },
                None,
            ),
        ],
    )
    def test_validate_taxonomy(self, taxonomy_data, expected_error):
        """Test the validate_taxonomy utility function."""
        errors = validate_taxonomy(taxonomy_data)
        if expected_error:
            assert expected_error in errors
        else:
            assert not errors

    @pytest.mark.parametrize(
        "name,expected_type",
        [
            ("Yellowstone National Park, USA", "park"),
            ("Willamette National Forest, Oregon", "forest"),
            ("Lane Co., Oregon", "county"),
            ("Portland, Oregon, USA", "city"),
            ("Random Place", "unknown"),
        ],
    )
    def test_determine_location_type(self, name: str, expected_type: str):
        """Test the determine_location_type utility function."""
        assert determine_location_type(name) == expected_type

    def test_parse_location_hierarchy(self):
        """Test the parse_location_hierarchy utility function."""
        location = "Mount Hood, Clackamas Co., Oregon, USA"
        hierarchy = parse_location_hierarchy(location)

        assert hierarchy["place"] == "Mount Hood"
        assert hierarchy["county"] == "Clackamas Co."
        assert hierarchy["state"] == "Oregon"
        assert hierarchy["country"] == "USA"


class TestPerformanceMonitoring:
    @pytest.mark.asyncio
    async def test_measure_performance_decorator(self):
        """Test performance monitoring decorator."""

        @measure_performance
        async def test_function(wait_time: float):
            await asyncio.sleep(wait_time)
            return "test"

        # Test with short wait time
        start_time = datetime.now()
        result = await test_function(0.1)
        end_time = datetime.now()

        assert result == "test"  # Function should work normally
        duration = (end_time - start_time).total_seconds()
        assert duration >= 0.1  # Should take at least our wait time

    @pytest.mark.asyncio
    async def test_measure_performance_error_handling(self):
        """Test performance monitoring with errors."""

        @measure_performance
        async def failing_function():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            await failing_function()


class TestDataValidation:
    def test_clean_text_fields(self, utility_config):
        """Test text field cleaning."""
        pipeline = DataPipeline(utility_config)

        test_cases = [
            ("<p>Test HTML</p>", "Test HTML"),  # HTML removal
            ("Line 1\n\nLine 2", "Line 1\nLine 2"),  # Newline normalization
            ("  Extra  Spaces  ", "Extra Spaces"),  # Space normalization
            ("Test―em dash", "Test--em dash"),  # Em dash conversion
            ("!image 123/test.jpg!", "[Image: test.jpg]"),  # Image tag conversion
            ("", None),  # Empty string handling
            (None, None),  # None handling
        ]

        for input_text, expected in test_cases:
            result = pipeline._clean_text(input_text)
            assert result == expected

    def test_validate_taxonomy(self, utility_config):
        """Test taxonomic validation."""
        pipeline = DataPipeline(utility_config)

        valid_taxonomy = {
            "kingdom": "Fungi",
            "phylum": "Basidiomycota",
            "class": "Agaricomycetes",
            "order": "Agaricales",
            "family": "Amanitaceae",
            "genus": "Amanita",
        }

        invalid_taxonomy = {
            "kingdom": "invalid",
            "phylum": "",
            "class": None,
            "order": "Agaricales",
            "family": "",
            "genus": "Amanita",
        }

        # Test valid taxonomy
        result = pipeline._standardize_classifications([valid_taxonomy])[0]
        assert result["kingdom"] == "Fungi"
        assert result["taxonomic_completeness"] == 1.0

        # Test invalid taxonomy
        result = pipeline._standardize_classifications([invalid_taxonomy])[0]
        assert result["taxonomic_completeness"] < 0.5

    def test_validate_coordinates(self, utility_config):
        """Test coordinate validation."""
        pipeline = DataPipeline(utility_config)

        valid_location = {
            "north": "45.5",
            "south": "45.4",
            "east": "-122.5",
            "west": "-122.6",
        }

        invalid_location = {
            "north": "invalid",
            "south": "",
            "east": None,
            "west": "-122.6",
        }

        # Test valid coordinates
        result = pipeline._process_locations_record(valid_location)
        assert result is not None
        assert result["north"] == 45.5
        assert result["center_lat"] == 45.45  # Average of north and south

        # Test invalid coordinates
        result = pipeline._process_locations_record(invalid_location)
        assert result is not None
        assert result["north"] is None
        assert result["center_lat"] is None


class TestDataAggregation:
    def test_aggregate_descriptions(self, utility_config):
        """Test description aggregation."""
        pipeline = DataPipeline(utility_config)

        descriptions = [
            {
                "source_type": 0,  # System source (highest priority)
                "source_name": "System",
                "general_description": "Primary description",
                "habitat": "Primary habitat",
                "notes": "System notes",
            },
            {
                "source_type": 1,  # User source
                "source_name": "User 1",
                "general_description": "Secondary description",
                "habitat": "Secondary habitat",
                "uses": "Medicinal",  # Unique field in second source
            },
        ]

        result = pipeline._aggregate_species_descriptions(descriptions)

        # Should use primary description from system source
        assert result["general"] == "Primary description"
        assert result["habitat"] == "Primary habitat"
        # Should include unique fields from secondary source
        assert "uses" in result
        assert result["uses"] == "Medicinal"
        # Should track sources
        assert len(result["sources"]) == 2

    def test_aggregate_empty_descriptions(self, utility_config):
        """Test aggregation with empty descriptions."""
        pipeline = DataPipeline(utility_config)

        result = pipeline._aggregate_species_descriptions([])
        assert result == {}

    def test_aggregate_location_descriptions(self, utility_config):
        """Test location description aggregation."""
        pipeline = DataPipeline(utility_config)

        descriptions = [
            {
                "source_type": 0,
                "source_name": "System",
                "gen_desc": "Primary description",
                "ecology": "Primary ecology",
                "species": "Species list 1",
            },
            {
                "source_type": 1,
                "source_name": "User",
                "gen_desc": "Secondary description",
                "species": "Species list 2",
                "notes": "Additional notes",  # Unique field
            },
        ]

        result = pipeline._aggregate_location_descriptions(descriptions)

        assert result["general"] == "Primary description"
        assert result["ecology"] == "Primary ecology"
        assert "notes" in result
        assert len(result["sources"]) == 2


class TestErrorHandling:
    def test_handle_invalid_files(self, utility_config, tmp_path):
        """Test handling of invalid files."""
        pipeline = DataPipeline(utility_config)

        # Test nonexistent file
        nonexistent_file = tmp_path / "nonexistent.csv"
        assert not pipeline._find_alternative_path("nonexistent.csv", tmp_path)

        # Test empty file
        empty_file = tmp_path / "empty.csv"
        empty_file.touch()
        assert pipeline._find_alternative_path("empty.csv", tmp_path) == empty_file

    def test_handle_invalid_json(self, utility_config):
        """Test handling of invalid JSON data."""
        pipeline = DataPipeline(utility_config)

        # Test invalid species data
        invalid_species = [
            {"_id": None},  # Missing required fields
            {"_id": 1, "scientific_name": ""},  # Empty required field
            {},  # Empty document
        ]

        # Should not raise exception but log errors
        result = asyncio.run(pipeline.store_species_batch(invalid_species))
        assert result is True  # Operation should complete
        assert len(pipeline.errors) > 0  # Should log errors

    @pytest.mark.asyncio
    async def test_handle_database_errors(self, utility_config):
        """Test handling of database errors."""
        # Create pipeline with invalid database configuration
        invalid_config = DataConfig(
            MONGODB_URI="mongodb://invalid:27017",
            DATABASE_NAME="invalid_db",
            BATCH_SIZE=100,
        )

        pipeline = DataPipeline(invalid_config)

        # Attempt operations with invalid database
        species_data = [{"_id": 1, "name": "Test Species"}]

        # Should handle database errors gracefully
        result = await pipeline.store_species_batch(species_data)
        assert result is True  # Operation should complete
        assert len(pipeline.errors) > 0  # Should log errors

        # Data should be stored in memory when database is unavailable
        assert "species" in pipeline.data_storage
        assert len(pipeline.data_storage["species"]) > 0


class TestProgressTracking:
    def test_progress_tracking(self, utility_config):
        """Test pipeline progress tracking."""
        pipeline = DataPipeline(utility_config)

        # Initial state
        assert pipeline.progress.total == 0
        assert pipeline.progress.processed == 0
        assert pipeline.progress.success == 0
        assert pipeline.progress.errors == 0

        # Mark progress
        pipeline.progress.total = 10
        pipeline.progress.processed = 5
        pipeline.progress.success = 4
        pipeline.progress.errors = 1

        # Test progress calculation
        assert pipeline.progress.processed == 5
        assert pipeline.progress.errors == 1

        # Mark completion
        pipeline.progress.complete()
        assert pipeline.progress.processed == pipeline.progress.total


class TestMemoryManagement:
    @pytest.mark.asyncio
    async def test_memory_cleanup(self, utility_config):
        """Test memory management during processing."""
        pipeline = DataPipeline(utility_config)

        # Process large dataset
        large_data = [{"_id": i, "name": f"Test {i}"} for i in range(10000)]

        # Process in batches
        for i in range(0, len(large_data), 100):
            batch = large_data[i : i + 100]
            await pipeline.store_species_batch(batch)

            # Check memory usage after each batch
            if pipeline.db:
                # If using database, memory storage should be minimal
                assert (
                    "species" not in pipeline.data_storage
                    or len(pipeline.data_storage["species"]) == 0
                )
            else:
                # If using memory storage, should have all processed records
                assert len(pipeline.data_storage["species"]) == i + len(batch)
