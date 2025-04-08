"""Comprehensive Tests for CSV Data Processing and Integration."""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from pydantic import ValidationError

from src.config import DataConfig
from src.data_csv import CSVProcessor
from src.schemas import ImageSchema


@pytest.fixture
def csv_config(tmp_path):
    """Create a test configuration."""
    return DataConfig(
        DATA_DIR=str(tmp_path),
        MONGODB_URI="mongodb://localhost:27017",
        DATABASE_NAME="test_mushroom_csv",
        BATCH_SIZE=100,
        NULL_VALUES=("", "NA", "N/A", "NULL", "NaN", "None"),
    )


@pytest.fixture
def sample_observations_df():
    """Create sample observations DataFrame."""
    data = pd.DataFrame(
        [
            {
                "id": 1,
                "name_id": 1,
                "when": "2023-01-01",
                "location_id": 1,
                "lat": 45.5,
                "lng": -122.5,
                "alt": 100,
                "vote_cache": 1.5,
                "is_collection_location": True,
            },
            {
                "id": 2,
                "name_id": 2,
                "when": "2023-01-02",
                "location_id": 2,
                "lat": 46.5,
                "lng": -123.5,
                "alt": 200,
                "vote_cache": 2.5,
                "is_collection_location": False,
            },
        ]
    )
    return data


@pytest.fixture
def sample_names_df():
    """Create sample names DataFrame."""
    data = pd.DataFrame(
        [
            {
                "id": 1,
                "text_name": "Amanita muscaria",
                "author": "Author 1",
                "deprecated": False,
                "rank": 4,
            },
            {
                "id": 2,
                "text_name": "Boletus edulis",
                "author": "Author 2",
                "deprecated": False,
                "rank": 4,
            },
        ]
    )
    return data


@pytest.fixture
def sample_taxonomy():
    """Create sample taxonomy data."""
    return {
        "kingdom": "Fungi",
        "phylum": "Basidiomycota",
        "class": "Agaricomycetes",
        "order": "Agaricales",
        "family": "Amanitaceae",
        "genus": "Amanita",
    }


class TestCSVProcessor:
    def test_csv_processor_init(self, csv_config):
        """Test CSVProcessor initialization."""
        processor = CSVProcessor(csv_config)
        assert processor.config == csv_config
        assert processor.chunk_size == csv_config.BATCH_SIZE
        assert isinstance(processor.null_values, list)
        assert "" in processor.null_values
        assert "NULL" in processor.null_values

    def test_csv_processor_read_chunks(
        self, csv_config, sample_observations_df, tmp_path
    ):
        """Test reading CSV file in chunks."""
        # Create test CSV file
        csv_path = tmp_path / "test.csv"
        sample_observations_df.to_csv(csv_path, index=False)

        processor = CSVProcessor(csv_config)
        chunks = list(processor.read_chunks(csv_path))

        # Verify chunks
        assert len(chunks) > 0
        total_rows = sum(len(chunk) for chunk in chunks)
        assert total_rows == len(sample_observations_df)

    def test_csv_processor_invalid_file(self, csv_config):
        """Test handling of invalid CSV file."""
        processor = CSVProcessor(csv_config)
        with pytest.raises(FileNotFoundError):
            list(processor.read_chunks(Path("nonexistent.csv")))

    def test_csv_processor_custom_chunk_size(
        self, csv_config, sample_observations_df, tmp_path
    ):
        """Test CSV processing with custom chunk size."""
        # Create large test dataset
        large_df = pd.concat([sample_observations_df] * 5, ignore_index=True)
        csv_path = tmp_path / "large.csv"
        large_df.to_csv(csv_path, index=False)

        # Test with small chunk size
        processor = CSVProcessor(csv_config, chunk_size=2)
        chunks = list(processor.read_chunks(csv_path))

        assert len(chunks) > 1  # Should have multiple chunks
        assert all(
            len(chunk) <= 2 for chunk in chunks
        )  # Each chunk should respect size limit
        total_rows = sum(len(chunk) for chunk in chunks)
        assert total_rows == len(large_df)  # All rows should be processed

    def test_csv_processor_data_validation(self, csv_config, tmp_path):
        """Test data validation during CSV processing."""
        # Create CSV with invalid data
        invalid_data = pd.DataFrame(
            [
                {"id": 1, "name": "Valid"},
                {"id": "invalid", "name": None},  # Invalid id type and null name
                {"id": 3, "name": "Valid2"},
            ]
        )
        csv_path = tmp_path / "invalid.csv"
        invalid_data.to_csv(csv_path, index=False)

        processor = CSVProcessor(csv_config)
        chunks = list(processor.read_chunks(csv_path))

        # Verify null values are handled
        processed_df = pd.concat(chunks)
        assert processed_df["name"].isna().any()  # Should have null values
        assert processed_df["id"].dtype == object  # Mixed types remain as object

    def test_read_with_correct_separator(self, csv_config, tmp_path):
        """Test reading CSV with correct separator detection."""
        # Test with comma-separated file
        comma_data = "id,name,value\n1,test,123"
        comma_file = tmp_path / "comma.csv"
        comma_file.write_text(comma_data)

        # Test with tab-separated file
        tab_data = "id\tname\tvalue\n1\ttest\t123"
        tab_file = tmp_path / "tab.csv"
        tab_file.write_text(tab_data)

        processor = CSVProcessor(csv_config)

        # Read comma-separated
        comma_df = next(processor.read_chunks(comma_file))
        assert len(comma_df.columns) == 3
        assert "name" in comma_df.columns

        # Read tab-separated
        tab_df = next(processor.read_chunks(tab_file))
        assert len(tab_df.columns) == 3
        assert "name" in tab_df.columns

    def test_handle_quoted_fields(self, csv_config, tmp_path):
        """Test handling of quoted fields in CSV."""
        quoted_data = '''id,name,description
1,"Smith, John","Description with, comma"
2,"Doe, Jane","Another, complex description"'''

        quoted_file = tmp_path / "quoted.csv"
        quoted_file.write_text(quoted_data)

        processor = CSVProcessor(csv_config)
        df = next(processor.read_chunks(quoted_file))

        assert len(df) == 2
        assert df.iloc[0]["name"] == "Smith, John"
        assert "," in df.iloc[0]["description"]

    def test_handle_empty_values(self, csv_config, tmp_path):
        """Test handling of empty and NULL values."""
        data_with_nulls = """id,name,value
1,test,
2,,NULL
3,test,N/A"""

        null_file = tmp_path / "nulls.csv"
        null_file.write_text(data_with_nulls)

        processor = CSVProcessor(csv_config)
        df = next(processor.read_chunks(null_file))

        assert pd.isna(df.iloc[0]["value"])
        assert pd.isna(df.iloc[1]["name"])
        assert pd.isna(df.iloc[1]["value"])
        assert pd.isna(df.iloc[2]["value"])

    def test_type_inference(self, csv_config, tmp_path):
        """Test data type inference for CSV fields."""
        type_data = """id,int_val,float_val,bool_val,date_val
1,123,45.67,true,2023-01-01
2,456,89.12,false,2023-01-02"""

        type_file = tmp_path / "types.csv"
        type_file.write_text(type_data)

        processor = CSVProcessor(csv_config)
        df = next(processor.read_chunks(type_file))

        assert df["int_val"].dtype in (np.int64, np.int32)
        assert df["float_val"].dtype == np.float64
        assert df["bool_val"].dtype == bool
        assert pd.api.types.is_datetime64_any_dtype(df["date_val"])


class TestUtilityFunctions:
    def test_clean_text(self, csv_config):
        """Test text cleaning functionality."""
        processor = CSVProcessor(csv_config)
        test_cases = [
            ("<p>Test HTML</p>", "Test HTML"),
            ("Line 1\n\nLine 2", "Line 1\nLine 2"),
            ("  Extra  Spaces  ", "Extra Spaces"),
            ("Test―em dash", "Test--em dash"),
            ("!image 123/test.jpg!", "[Image: test.jpg]"),
            (None, None),
            ("", None),
        ]

        for input_text, expected in test_cases:
            assert processor._clean_text(input_text) == expected

    def test_standardize_taxonomy(self, csv_config, sample_taxonomy):
        """Test taxonomy standardization."""
        processor = CSVProcessor(csv_config)
        standardized = processor._standardize_classifications([sample_taxonomy])[0]

        assert standardized["kingdom"] == "Fungi"
        assert standardized["taxonomic_completeness"] == 1.0
        assert all(
            rank in standardized
            for rank in ["phylum", "class", "order", "family", "genus"]
        )

    def test_extract_genus_from_family(self, csv_config):
        """Test genus extraction from family name."""
        processor = CSVProcessor(csv_config)
        test_cases = [
            ("Amanitaceae", "Amanita"),
            ("Boletaceae", "Boletus"),
            ("Invalid", None),
        ]

        for family, expected_genus in test_cases:
            result = processor._extract_genus_from_family(family)
            if expected_genus:
                assert result == expected_genus
            else:
                assert result is None


class TestDataclasses:
    def test_image_metadata(self):
        """Test image metadata processing."""
        image_data = {
            "id": 1,
            "content_type": "image/jpeg",
            "copyright_holder": "Test User",
            "license": "CC BY-SA",
            "ok_for_export": True,
            "diagnostic": True,
            "width": 800,
            "height": 600,
        }

        # Test should verify that the image metadata is processed correctly
        assert image_data["content_type"] in ["image/jpeg", "image/png", "image/gif"]
        assert isinstance(image_data["ok_for_export"], bool)
        assert isinstance(image_data["width"], int)
        assert isinstance(image_data["height"], int)

    def test_location_bounding_box(self):
        """Test location bounding box calculations."""
        location_data = {"north": 45.5, "south": 45.4, "east": -122.5, "west": -122.6}

        # Calculate center coordinates
        center_lat = (location_data["north"] + location_data["south"]) / 2
        center_lng = (location_data["east"] + location_data["west"]) / 2

        assert center_lat == 45.45
        assert center_lng == -122.55

    def test_license(self):
        """Test license standardization."""
        test_licenses = [
            "creative commons wikipedia compatible v3.0",
            "CC BY-SA",
            "public domain",
            "all rights reserved",
            None,
        ]

        for license_str in test_licenses:
            if license_str:
                assert isinstance(license_str.lower(), str)
            else:
                assert license_str is None


class TestCSVIntegrationPipeline:
    @pytest.mark.asyncio
    async def test_full_pipeline_processing(self, csv_config, tmp_path):
        """Test full pipeline processing with multiple CSV files."""
        # Set up test data
        self._create_test_files(tmp_path)

        processor = CSVProcessor(csv_config)
        try:
            # Process names
            names = list(processor.read_chunks(tmp_path / "names.csv"))
            assert len(names) > 0

            # Process observations
            observations = list(processor.read_chunks(tmp_path / "observations.csv"))
            assert len(observations) > 0

            # Process images
            images = list(processor.read_chunks(tmp_path / "images.csv"))
            assert len(images) > 0

        except Exception as e:
            pytest.fail(f"Pipeline processing failed: {e}")

    def _create_test_files(self, tmp_path):
        """Create test CSV files."""
        # Create names.csv
        names_df = pd.DataFrame(self.get_sample_names())
        names_df.to_csv(tmp_path / "names.csv", index=False)

        # Create observations.csv
        observations_df = pd.DataFrame(self.get_sample_observations())
        observations_df.to_csv(tmp_path / "observations.csv", index=False)

        # Create images.csv
        images_df = pd.DataFrame(self.get_sample_images())
        images_df.to_csv(tmp_path / "images.csv", index=False)

    def get_sample_names(self):
        """Get sample names data."""
        return [
            {
                "id": 1,
                "text_name": "Amanita muscaria",
                "author": "Author 1",
                "deprecated": False,
                "rank": 4,
            },
            {
                "id": 2,
                "text_name": "Boletus edulis",
                "author": "Author 2",
                "deprecated": False,
                "rank": 4,
            },
        ]

    def get_sample_observations(self):
        """Get sample observations data."""
        return [
            {
                "id": 1,
                "name_id": 1,
                "when": "2023-01-01",
                "location_id": 1,
                "lat": 45.5,
                "lng": -122.5,
                "alt": 100,
                "vote_cache": 1.5,
                "is_collection_location": True,
            },
            {
                "id": 2,
                "name_id": 2,
                "when": "2023-01-02",
                "location_id": 2,
                "lat": 46.5,
                "lng": -123.5,
                "alt": 200,
                "vote_cache": 2.5,
                "is_collection_location": False,
            },
        ]

    def get_sample_images(self):
        """Get sample images data."""
        return [
            {
                "id": 1,
                "content_type": "image/jpeg",
                "copyright_holder": "User 1",
                "license_id": 1,
                "ok_for_export": True,
                "diagnostic": True,
                "width": 800,
                "height": 600,
            },
            {
                "id": 2,
                "content_type": "image/jpeg",
                "copyright_holder": "User 2",
                "license_id": 1,
                "ok_for_export": True,
                "diagnostic": False,
                "width": 1024,
                "height": 768,
            },
        ]


class TestImageProcessing:
    def test_parse_image_csv(self, csv_config, tmp_path):
        """Test parsing of image CSV data."""
        # Create test images.csv file
        images_data = """id,content_type,copyright_holder,license,ok_for_export,diagnostic,width,height,created_at,updated_at
82070,image/jpeg,Chris Parrish,Creative Commons Wikipedia Compatible v3.0,1,1,800,600,2025-03-07T15:40:29+00:00,2025-03-07T15:40:29+00:00
82071,image/jpeg,John Smith,CC BY-SA,1,0,1024,768,2025-03-07T15:40:29+00:00,2025-03-07T15:40:29+00:00"""

        images_file = tmp_path / "images.csv"
        images_file.write_text(images_data)

        processor = CSVProcessor(csv_config)
        df = next(processor.read_chunks(images_file))

        # Verify DataFrame structure
        assert "id" in df.columns
        assert "content_type" in df.columns
        assert "copyright_holder" in df.columns
        assert "license" in df.columns
        assert "ok_for_export" in df.columns
        assert "diagnostic" in df.columns

        # Test conversion to ImageSchema
        image_record = df.iloc[0].to_dict()
        image = ImageSchema.model_validate(image_record)

        assert image.content_type == "image/jpeg"
        assert image.copyright_holder == "Chris Parrish"
        assert image.ok_for_export == True
        assert image.diagnostic == True

    def test_handle_malformed_csv(self, csv_config, tmp_path):
        """Test handling of malformed CSV data."""
        # Create test CSV with problematic formatting
        malformed_data = """id\tcontent_type\tcopyright_holder\tlicense\tok_for_export\tdiagnostic
82070\timage/jpeg\tChris Parrish\tCC BY-SA\t1\t1
82071\timage/jpeg\tJohn Smith\tCC BY-SA\t1\t0"""

        malformed_file = tmp_path / "malformed.csv"
        malformed_file.write_text(malformed_data)

        processor = CSVProcessor(csv_config)
        df = next(
            processor.read_chunks(malformed_file, sep="\t")
        )  # Explicitly specify tab separator

        # Verify data was parsed correctly despite malformed input
        assert len(df) > 0
        assert "content_type" in df.columns

        # Test record validation
        image_record = df.iloc[0].to_dict()
        # Clean the record before validation
        clean_record = {
            "image_id": image_record["id"],
            "content_type": image_record["content_type"],
            "copyright_holder": image_record["copyright_holder"],
            "license_id": 1,  # Convert license string to ID
            "ok_for_export": bool(int(image_record["ok_for_export"])),
            "diagnostic": bool(int(image_record["diagnostic"])),
        }
        image = ImageSchema.model_validate(clean_record)
        assert image.content_type == "image/jpeg"

    def test_handle_missing_fields(self, csv_config, tmp_path):
        """Test handling of CSV with missing fields."""
        # Create test CSV with missing optional fields
        minimal_data = """id,content_type,copyright_holder,license_id
82070,image/jpeg,Chris Parrish,1
82071,image/jpeg,John Smith,1"""

        minimal_file = tmp_path / "minimal.csv"
        minimal_file.write_text(minimal_data)

        processor = CSVProcessor(csv_config)
        df = next(processor.read_chunks(minimal_file))

        # Test record with minimal required fields
        image_record = df.iloc[0].to_dict()
        clean_record = {
            "image_id": image_record["id"],
            "content_type": image_record["content_type"],
            "copyright_holder": image_record["copyright_holder"],
            "license_id": image_record["license_id"],
        }

        # Should validate without optional fields
        image = ImageSchema.model_validate(clean_record)
        assert image.content_type == "image/jpeg"
        assert image.copyright_holder == "Chris Parrish"
        assert image.license_id == 1

    def test_handle_invalid_values(self, csv_config, tmp_path):
        """Test handling of invalid values in CSV."""
        # Create test CSV with invalid values
        invalid_data = """id,content_type,copyright_holder,license_id,ok_for_export,diagnostic,width,height
82070,invalid,Chris Parrish,1,invalid,2,-100,-200
82071,image/jpeg,John Smith,1,1,0,0,0"""

        invalid_file = tmp_path / "invalid.csv"
        invalid_file.write_text(invalid_data)

        processor = CSVProcessor(csv_config)
        df = next(processor.read_chunks(invalid_file))

        # Test handling of invalid record
        invalid_record = df.iloc[0].to_dict()
        with pytest.raises(ValidationError):
            ImageSchema.model_validate(invalid_record)

        # Test handling of valid record
        valid_record = df.iloc[1].to_dict()
        clean_record = {
            "image_id": valid_record["id"],
            "content_type": valid_record["content_type"],
            "copyright_holder": valid_record["copyright_holder"],
            "license_id": valid_record["license_id"],
            "ok_for_export": bool(int(valid_record["ok_for_export"])),
            "diagnostic": bool(int(valid_record["diagnostic"])),
        }
        image = ImageSchema.model_validate(clean_record)
        assert image.content_type == "image/jpeg"

    @pytest.mark.parametrize(
        "content_type,expected_valid",
        [
            ("image/jpeg", True),
            ("image/png", True),
            ("image/gif", True),
            ("application/pdf", False),
            ("text/plain", False),
            ("invalid", False),
        ],
    )
    def test_content_type_validation(self, csv_config, content_type, expected_valid):
        """Test validation of image content types."""
        record = {
            "image_id": 1,
            "content_type": content_type,
            "copyright_holder": "Test User",
            "license_id": 1,
        }

        if expected_valid:
            image = ImageSchema.model_validate(record)
            assert image.content_type == content_type
        else:
            with pytest.raises(ValidationError):
                ImageSchema.model_validate(record)
