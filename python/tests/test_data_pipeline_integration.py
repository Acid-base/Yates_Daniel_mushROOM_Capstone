"""Comprehensive Tests for CSV Data Processing and Integration."""

import pytest
import pandas as pd
import numpy as npt Path
from pathlib import Path Any, List
from pydantic import ValidationError
from src.config import DataConfig
from src.config import DataConfigaPipeline
from src.data_csv import CSVProcessor
from src.schemas import ImageSchema
class TestCSVIntegrationPipeline:
    """Test class for CSV integration pipeline."""
@pytest.fixture
def csv_config(tmp_path):
    """Create a test configuration."""_path):
    return DataConfig( pipeline instance."""
        DATA_DIR=str(tmp_path),
        MONGODB_URI="mongodb://localhost:27017",
        DATABASE_NAME="test_mushroom_csv",st:27017",
        BATCH_SIZE=100,ME="test_mushroom_integration",
        NULL_VALUES=("", "NA", "N/A", "NULL", "NaN", "None"),
    )       NULL_VALUES=("", "NA", "N/A", "NULL", "NaN", "None"),
        )
        return DataPipeline(config)
@pytest.fixture
def sample_observations_df():
    """Create sample observations DataFrame."""ath):
    data = pd.DataFrame(SV files."""
        [ntegration_files = {
            {names.csv": [
                "id": 1,
                "name_id": 1,
                "when": "2023-01-01",nita muscaria",
                "location_id": 1,thor 1",
                "lat": 45.5,ted": False,
                "lng": -122.5,
                "alt": 100,
                "vote_cache": 1.5,
                "is_collection_location": True,
            },  {
            {       "id": 1,
                "id": 2,e_id": 1,
                "name_id": 2,2023-01-01",
                "when": "2023-01-02",
                "location_id": 2,
                "lat": 46.5,122.5,
                "lng": -123.5,
                "alt": 200,
                "vote_cache": 2.5,
                "is_collection_location": False,
            },      "id": 1,
        ]           "content_type": "image/jpeg",
    )               "copyright_holder": "User 1",
    return data     "license_id": 1,
                }
            ]
@pytest.fixture
def sample_names_df():
    """Create sample names DataFrame."""n_files.items():
    data = pd.DataFrame(tmp_path / filename
        [   pd.DataFrame(data).to_csv(file_path, index=False)
            {
                "id": 1,on_files
                "text_name": "Amanita muscaria",
                "author": "Author 1",
                "deprecated": False,ng(self, pipeline_integration, setup_integration_csv_files, tmp_path):
                "rank": 4,ine processing."""
            },lename in setup_integration_csv_files.keys():
            {ile_path = tmp_path / filename
                "id": 2, filename.replace(".csv", "")
                "text_name": "Boletus edulis",on.process_csv_file(file_path, table_name)
                "author": "Author 2",to process {filename}"
                "deprecated": False,
                "rank": 4,e(config: DataConfig, input_files: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
            }, data pipeline with provided configuration and input files."""
        ]ine = DataPipeline(config)
    )
    return dataach input file
    for filename, data in input_files.items():
        file_path = Path(config.DATA_DIR) / filename
@pytest.fixtureFrame(data).to_csv(file_path, index=False)
def sample_taxonomy():
    """Create sample taxonomy data."""".csv", "")
    return {ess = await pipeline.process_csv_file(file_path, table_name)
        "kingdom": "Fungi",
        "phylum": "Basidiomycota",ailed to process {filename}")
        "class": "Agaricomycetes",
        "order": "Agaricales",ge
        "family": "Amanitaceae",
        "genus": "Amanita",
    }tegration tests for the full data pipeline flow (using real CSV processing)."""

import pytest
class TestCSVProcessor:
    def test_csv_processor_init(self, csv_config):ing functions (replace with your actual imports)
        """Test CSVProcessor initialization."""
        processor = CSVProcessor(csv_config)
        assert processor.config == csv_config
        assert processor.chunk_size == csv_config.BATCH_SIZE
        assert isinstance(processor.null_values, list)ts) ---
        assert "" in processor.null_values
        assert "NULL" in processor.null_valuesfic config for integration tests
    """Fixture for DataConfig for integration tests, creates test data directory."""
    def test_csv_processor_read_chunks(
        self, csv_config, sample_observations_df, tmp_path
    ): # Separate dir for integration tests
        """Test reading CSV file in chunks."""
        # Create test CSV file
        csv_path = tmp_path / "test.csv"7",
        sample_observations_df.to_csv(csv_path, index=False)for integration tests
        DATA_DIR=test_data_dir,
        processor = CSVProcessor(csv_config)
        chunks = list(processor.read_chunks(csv_path))
    )
        # Verify chunks
        assert len(chunks) > 0
        total_rows = sum(len(chunk) for chunk in chunks)
        assert total_rows == len(sample_observations_df)
    """Fixture to create DataPipeline instance for integration tests."""
    def test_csv_processor_invalid_file(self, csv_config):
        """Test handling of invalid CSV file."""
        processor = CSVProcessor(csv_config)mple
        with pytest.raises(FileNotFoundError):
            list(processor.read_chunks(Path("nonexistent.csv")))
    uses
    def test_csv_processor_custom_chunk_size(
        self, csv_config, sample_observations_df, tmp_path
    ):me interesting notes about Agaricus bisporus.
        """Test CSV processing with custom chunk size."""
        # Create large test datasetcus_bisporus.html
        large_df = pd.concat([sample_observations_df] * 5, ignore_index=True)
        csv_path = tmp_path / "large.csv"
        large_df.to_csv(csv_path, index=False)
    3
        # Test with small chunk size
        processor = CSVProcessor(csv_config, chunk_size=2)
        chunks = list(processor.read_chunks(csv_path))
    1
        assert len(chunks) > 1  # Should have multiple chunks
        assert all(e
            len(chunk) <= 2 for chunk in chunks
        )  # Each chunk should respect size limitroup.
        total_rows = sum(len(chunk) for chunk in chunks)
        assert total_rows == len(large_df)  # All rows should be processed
    habitat
    def test_csv_processor_data_validation(self, csv_config, tmp_path):
        """Test data validation during CSV processing."""
        # Create CSV with invalid data
        invalid_data = pd.DataFrame(
            [ome caution advised.
                {"id": 1, "name": "Valid"},
                {"id": "invalid", "name": None},  # Invalid id type and null name
                {"id": 3, "name": "Valid2"},
            ] for Agaricus campestris group.
        )
        csv_path = tmp_path / "invalid.csv"
        invalid_data.to_csv(csv_path, index=False)me_id\tdomain\tkingdom\tphylum\tclass\torder\tfamily
    1\t1\tEukaryota\tFungi\t\t\t\t
        processor = CSVProcessor(csv_config)garicomycetes\tAgaricales\tAgaricaceae
        chunks = list(processor.read_chunks(csv_path))tes\tAgaricales\tAgaricaceae
    4\t4\tEukaryota\tFungi\tBasidiomycota\tAgaricomycetes\tAgaricales\tAgaricaceae
        # Verify null values are handleda\tAgaricomycetes\tAgaricales\tAgaricaceae
        processed_df = pd.concat(chunks)a\tAgaricomycetes\tAgaricales\tBoletaceae
        assert processed_df["name"].isna().any()  # Should have null valuesaceae
        assert processed_df["id"].dtype == object  # Mixed types remain as objectaceae
    9\t9\tEukaryota\tFungi\tBasidiomycota\tAgaricomycetes\tAgaricales\tAmanitaceae
    def test_read_with_correct_separator(self, csv_config, tmp_path):es\tAmanitaceae
        """Test reading CSV with correct separator detection."""iales\tClavariaceae
        # Test with comma-separated fileota\tAgaricomycetes\tGomphales\tClavariadelphaceae
        comma_data = "id,name,value\n1,test,123"gnoliopsida\tRosales\tRosaceae
        comma_file = tmp_path / "comma.csv"
        comma_file.write_text(comma_data)
    def test_data_pipeline_integration_real_csv(
        # Test with tab-separated filetup_integration_csv_files
        tab_data = "id\tname\tvalue\n1\ttest\t123"
        tab_file = tmp_path / "tab.csv"to-end with real CSV processing (integration test)."""
        tab_file.write_text(tab_data)on
        output_json_list = run_data_pipeline(config)  # Run the data pipeline
        processor = CSVProcessor(csv_config)
        # --- Assertions - Similar to test_csv_integration.py, but now testing full pipeline ---
        # Read comma-separated ran without errors (implicitly checked if no exceptions are raised)
        comma_df = next(processor.read_chunks(comma_file))
        assert len(comma_df.columns) == 3 JSON documents
        assert "name" in comma_df.columnst, list), "Output should be a list"
        assert all(isinstance(doc, dict) for doc in output_json_list), (
        # Read tab-separatedtput should be a dict (JSON document)"
        tab_df = next(processor.read_chunks(tab_file))
        assert len(tab_df.columns) == 3
        assert "name" in tab_df.columnsty (at least some species processed from test data)
        assert output_json_list, (
    def test_handle_quoted_fields(self, csv_config, tmp_path): processed"
        """Test handling of quoted fields in CSV."""
        quoted_data = '''id,name,description
1,"Smith, John","Description with, comma"ent and validate its content
2,"Doe, Jane","Another, complex description"'''
        for doc in output_json_list:
        quoted_file = tmp_path / "quoted.csv""Agaricus bisporus":
        quoted_file.write_text(quoted_data)
                break
        processor = CSVProcessor(csv_config)
        df = next(processor.read_chunks(quoted_file))output"
        )
        assert len(df) == 2
        assert df.iloc[0]["name"] == "Smith, John"ontent (more comprehensive assertions needed here!)
        assert "," in df.iloc[0]["description"]== "Agaricus bisporus"
        assert agaricus_doc["rank"] == 20
    def test_handle_empty_values(self, csv_config, tmp_path):
        """Test handling of empty and NULL values."""s bisporus"
        data_with_nulls = """id,name,value["general"]
1,test, )
2,,NULL assert "Agaricaceae" in agaricus_doc["classification"]["family"]
3,test,N/A""" ADD MORE DETAILED ASSERTIONS HERE to validate more fields, aggregated data, data types, etc.
        # --- Based on your expected output structure and transformations defined in the wrangling report.
        null_file = tmp_path / "nulls.csv"
        null_file.write_text(data_with_nulls) 'deprecated' species in output
        species_names_in_output = [doc["scientific_name"] for doc in output_json_list]
        processor = CSVProcessor(csv_config)ot in species_names_in_output, (
        df = next(processor.read_chunks(null_file))
        )
        assert pd.isna(df.iloc[0]["value"])
        assert pd.isna(df.iloc[1]["name"])pecies_names_in_output
        assert pd.isna(df.iloc[1]["value"])
        assert pd.isna(df.iloc[2]["value"])
                doc["scientific_name"] for doc in output_json_list if doc["id"] == 5
    def test_type_inference(self, csv_config, tmp_path):
        """Test data type inference for CSV fields."""
        type_data = """id,int_val,float_val,bool_val,date_val
1,123,45.67,true,2023-01-01
2,456,89.12,false,2023-01-02"""test_data_pipeline_integration.py ---
# 1. **Crucially: Add more comprehensive assertions in `test_data_pipeline_integration_real_csv` to validate the *content* of the output JSON documents.**
        type_file = tmp_path / "types.csv"(description, classification, images, observation_summary if included), aggregated data, data types, etc.
        type_file.write_text(type_data)ocument` schema and the expected transformations from the wrangling report.
# 2. **Expand the test data (in `setup_integration_csv_files` and the `NAMES_CSV_TEST_DATA` etc. strings) to include data for *all* CSV files**, not just names, name_descriptions, and name_classifications.
        processor = CSVProcessor(csv_config)tion of the entire pipeline and all data sources.
        df = next(processor.read_chunks(type_file))ntegration tests.**  Include data that tests error handling and data cleaning logic at the pipeline level.
# 4. **Consider adding tests for API enrichment and database interaction within the integration tests** if you want to verify those aspects in a more integrated way (though mocking might still be preferred for speed and isolation in most integration tests, reserving real API/DB tests for separate E2E tests).
        assert df["int_val"].dtype in (np.int64, np.int32)
        assert df["float_val"].dtype == np.float64
        assert df["bool_val"].dtype == booldata pipeline with real/mock API and database."""
        assert pd.api.types.is_datetime64_any_dtype(df["date_val"])
import pytest
# You might need libraries for mocking API calls (e.g., httpx mock, requests-mock) and a test MongoDB instance
class TestUtilityFunctions:
    def test_clean_text(self, csv_config):ace with your actual imports)
        """Test text cleaning functionality."""
        processor = CSVProcessor(csv_config)
        test_cases = [ as needed for E2E tests - might need real/mock DB and API setup) ---
            ("<p>Test HTML</p>", "Test HTML"),
            ("Line 1\n\nLine 2", "Line 1\nLine 2"),
            ("  Extra  Spaces  ", "Extra Spaces"),."""
            ("Test―em dash", "Test--em dash"),
            ("!image 123/test.jpg!", "[Image: test.jpg]"),
            (None, None), Adjust DataConfig for E2E - potentially using a test MongoDB URI
            ("", None),ngodb://test:27017",  #  <- Replace with a test MongoDB URI or mock setup
        ]ATABASE_NAME="test_e2e_db",  # Separate DB for E2E tests
        DATA_DIR=test_data_dir,
        for input_text, expected in test_cases:
            assert processor._clean_text(input_text) == expected
        # ... potentially other config settings for E2E tests ...
    def test_standardize_taxonomy(self, csv_config, sample_taxonomy):
        """Test taxonomy standardization."""
        processor = CSVProcessor(csv_config)
        standardized = processor._standardize_classifications([sample_taxonomy])[0]
async def pipeline_e2e(csv_config_e2e):
        assert standardized["kingdom"] == "Fungi"r end-to-end tests."""
        assert standardized["taxonomic_completeness"] == 1.0 using Docker, or an in-memory DB)
        assert all(Pipeline(csv_config_e2e)
            rank in standardized
            for rank in ["phylum", "class", "order", "family", "genus"]
        )

    def test_extract_genus_from_family(self, csv_config):
        """Test genus extraction from family name."""
        processor = CSVProcessor(csv_config) for end-to-end tests."""
        test_cases = [fig_e2e.DATA_DIR
            ("Amanitaceae", "Amanita"),milar to setup_integration_csv_files, but potentially with more comprehensive data
            ("Boletaceae", "Boletus"),
            ("Invalid", None),sv (adjust content as needed for E2E tests)
        ]
        data_dir / "names.csv"
        for family, expected_genus in test_cases:ated\tcorrect_spelling_id\tsynonym_id\trank
            result = processor._extract_genus_from_family(family)
            if expected_genus:nge) Imbach\t0\t\t\t20
                assert result == expected_genus
            else:other CSV files as needed for E2E tests ...
                assert result is None


class TestDataclasses:E2E:  # Class for end-to-end tests
    def test_image_metadata(self):
        """Test image metadata processing."""w(self, pipeline_e2e, setup_e2e_csv_files):
        image_data = {omplete end-to-end data pipeline flow, including API and database interaction."""
            "id": 1,_config_e2e
            "content_type": "image/jpeg",ine(config)  # Run the data pipeline
            "copyright_holder": "Test User",
            "license": "CC BY-SA",ests ---
            "ok_for_export": True, without errors
            "diagnostic": True,
            "width": 800,put is a list of JSON documents
            "height": 600,
        } 3. Check if output is not empty

        # Test should verify that the image metadata is processed correctlyctly using pipeline.db client)
        assert image_data["content_type"] in ["image/jpeg", "image/png", "image/gif"]
        assert isinstance(image_data["ok_for_export"], bool)
        assert isinstance(image_data["width"], int)_NAME]["your_collection_name"]
        assert isinstance(image_data["height"], int).find_one({"scientific_name": "Agaricus bisporus"})
        #    assert agaricus_doc_from_db is not None
    def test_location_bounding_box(self):"rank"] == 20
        """Test location bounding box calculations."""a in the database against expected output ...
        location_data = {"north": 45.5, "south": 45.4, "east": -122.5, "west": -122.6}
        # 5. Validate API interactions (if you are mocking or recording API calls in E2E tests)
        # Calculate center coordinatesock):
        center_lat = (location_data["north"] + location_data["south"]) / 2
        center_lng = (location_data["east"] + location_data["west"]) / 2

        assert center_lat == 45.45tion phase."""
        assert center_lng == -122.55
import pandas as pd
    def test_license(self):
        """Test license standardization."""
        test_licenses = [ DataPipeline
            "creative commons wikipedia compatible v3.0",
            "CC BY-SA",
            "public domain",
            "all rights reserved",
            None,t configuration for integration tests."""
        ]n DataConfig(
        DATA_DIR=str(tmp_path),
        for license_str in test_licenses:27017",
            if license_str:_mushroom_integration",
                assert isinstance(license_str.lower(), str)
            else:ES=("", "NA", "N/A", "NULL", "NaN", "None"),
                assert license_str is None


class TestCSVIntegrationPipeline:
    @pytest.mark.asynciop_path):
    async def test_full_pipeline_processing(self, csv_config, tmp_path):
        """Test full pipeline processing with multiple CSV files."""
        # Set up test dataame(
        self._create_test_files(tmp_path)
            {
        processor = CSVProcessor(csv_config)
        try:    "text_name": "Amanita muscaria",
            # Process namesAuthor 1",
            names = list(processor.read_chunks(tmp_path / "names.csv"))
            assert len(names) > 0
            },
            # Process observations
            observations = list(processor.read_chunks(tmp_path / "observations.csv"))
            assert len(observations) > 0ulis",
                "author": "Author 2",
            # Process images: False,
            images = list(processor.read_chunks(tmp_path / "images.csv"))
            assert len(images) > 0
        ]
        except Exception as e:
            pytest.fail(f"Pipeline processing failed: {e}")sep="\t")

    def _create_test_files(self, tmp_path):
        """Create test CSV files."""
        # Create names.csv
        names_df = pd.DataFrame(self.get_sample_names())
        names_df.to_csv(tmp_path / "names.csv", index=False)
                "source_type": 0,
        # Create observations.csvystem",
        observations_df = pd.DataFrame(self.get_sample_observations())
        observations_df.to_csv(tmp_path / "observations.csv", index=False)
                "distribution": "Widespread",
        # Create images.csv"Under conifers",
        images_df = pd.DataFrame(self.get_sample_images())
        images_df.to_csv(tmp_path / "images.csv", index=False)
                "notes": "Iconic mushroom",
    def get_sample_names(self):
        """Get sample names data."""
        return ["id": 2,
            {   "name_id": 1,
                "id": 1,type": 1,
                "text_name": "Amanita muscaria",
                "author": "Author 1",: "Additional description",
                "deprecated": False,ods",
                "rank": 4,
            },
            {
                "id": 2,_csv(tmp_path / "name_descriptions.csv", index=False, sep="\t")
                "text_name": "Boletus edulis",
                "author": "Author 2",
                "deprecated": False,ame(
                "rank": 4,
            },
        ]       "name_id": 1,
                "kingdom": "Fungi",
    def get_sample_observations(self):ta",
        """Get sample observations data."""
        return ["order": "Agaricales",
            {   "family": "Amanitaceae",
                "id": 1, "Amanita",
                "name_id": 1,
                "when": "2023-01-01",
                "location_id": 1,
                "lat": 45.5,Fungi",
                "lng": -122.5,idiomycota",
                "alt": 100,garicomycetes",
                "vote_cache": 1.5,s",
                "is_collection_location": True,
            },  "genus": "Boletus",
            {,
                "id": 2,
                "name_id": 2,
                "when": "2023-01-02",
                "location_id": 2,cations.csv", index=False, sep="\t"
                "lat": 46.5,
                "lng": -123.5,
                "alt": 200,tions
                "vote_cache": 2.5,
                "is_collection_location": False,
            },
        ]       "id": 1,
                "name": "Test Forest",
    def get_sample_images(self):
        """Get sample images data."""
        return ["east": -122.5,
            {   "west": -122.6,
                "id": 1,on": "100-200",
                "content_type": "image/jpeg",
                "copyright_holder": "User 1",
                "license_id": 1,
                "ok_for_export": True,
                "diagnostic": True,ain",
                "width": 800,,
                "height": 600,
            },  "east": -121.5,
            {   "west": -121.6,
                "id": 2,on": "1000-2000",
                "content_type": "image/jpeg",
                "copyright_holder": "User 2",
                "license_id": 1,
                "ok_for_export": True,
                "diagnostic": False, "locations.csv", index=False, sep="\t")
                "width": 1024,
                "height": 768, = pd.DataFrame(
            },
        ]   {
                "id": 1,
                "location_id": 1,
class TestImageProcessing:pe": 0,
    def test_parse_image_csv(self, csv_config, tmp_path):
        """Test parsing of image CSV data."""est",
        # Create test images.csv fileushrooms present",
        images_data = """id,content_type,copyright_holder,license,ok_for_export,diagnostic,width,height,created_at,updated_at
82070,image/jpeg,Chris Parrish,Creative Commons Wikipedia Compatible v3.0,1,1,800,600,2025-03-07T15:40:29+00:00,2025-03-07T15:40:29+00:00
82071,image/jpeg,John Smith,CC BY-SA,1,0,1024,768,2025-03-07T15:40:29+00:00,2025-03-07T15:40:29+00:00"""
                "location_id": 2,
        images_file = tmp_path / "images.csv"
        images_file.write_text(images_data)at",
                "ecology": "Alpine forest",
        processor = CSVProcessor(csv_config)
        df = next(processor.read_chunks(images_file))
        ]
        # Verify DataFrame structure
        assert "id" in df.columns_csv(
        assert "content_type" in df.columnssv", index=False, sep="\t"
        assert "copyright_holder" in df.columns
        assert "license" in df.columns
        assert "ok_for_export" in df.columns
        assert "diagnostic" in df.columns
        [
        # Test conversion to ImageSchema
        image_record = df.iloc[0].to_dict()
        image = ImageSchema.model_validate(image_record)
                "when": "2023-01-01",
        assert image.content_type == "image/jpeg"
        assert image.copyright_holder == "Chris Parrish"
        assert image.ok_for_export == True
        assert image.diagnostic == True
                "vote_cache": 1.5,
    def test_handle_malformed_csv(self, csv_config, tmp_path):
        """Test handling of malformed CSV data."""
        # Create test CSV with problematic formatting
        malformed_data = """id\tcontent_type\tcopyright_holder\tlicense\tok_for_export\tdiagnostic
82070\timage/jpeg\tChris Parrish\tCC BY-SA\t1\t1
82071\timage/jpeg\tJohn Smith\tCC BY-SA\t1\t0"""
                "location_id": 2,
        malformed_file = tmp_path / "malformed.csv"
        malformed_file.write_text(malformed_data)
                "alt": 1500,
        processor = CSVProcessor(csv_config)
        df = next(s_collection_location": True,
            processor.read_chunks(malformed_file, sep="\t")
        )  # Explicitly specify tab separator
    )
        # Verify data was parsed correctly despite malformed inputFalse, sep="\t")
        assert len(df) > 0
        assert "content_type" in df.columns
    images_data = pd.DataFrame(
        # Test record validation
        image_record = df.iloc[0].to_dict()
        # Clean the record before validation
        clean_record = {_type": "image/jpeg",
            "image_id": image_record["id"],",
            "content_type": image_record["content_type"],
            "copyright_holder": image_record["copyright_holder"],
            "license_id": 1,  # Convert license string to ID
            "ok_for_export": bool(int(image_record["ok_for_export"])),
            "diagnostic": bool(int(image_record["diagnostic"])),
        }   },
        image = ImageSchema.model_validate(clean_record)
        assert image.content_type == "image/jpeg"
                "content_type": "image/jpeg",
    def test_handle_missing_fields(self, csv_config, tmp_path):
        """Test handling of CSV with missing fields."""
        # Create test CSV with missing optional fields
        minimal_data = """id,content_type,copyright_holder,license_id
82070,image/jpeg,Chris Parrish,1
82071,image/jpeg,John Smith,1"""
            },
        minimal_file = tmp_path / "minimal.csv"
        minimal_file.write_text(minimal_data)
    images_data.to_csv(tmp_path / "images.csv", index=False, sep="\t")
        processor = CSVProcessor(csv_config)
        df = next(processor.read_chunks(minimal_file))
        [
        # Test record with minimal required fieldsrank": 1},
        image_record = df.iloc[0].to_dict()": 2, "rank": 2},
        clean_record = {
            "image_id": image_record["id"],
            "content_type": image_record["content_type"],
            "copyright_holder": image_record["copyright_holder"],t"
            "license_id": image_record["license_id"],
        }
    return tmp_path
        # Should validate without optional fields
        image = ImageSchema.model_validate(clean_record)
        assert image.content_type == "image/jpeg"
        assert image.copyright_holder == "Chris Parrish"fig, integration_files):
        assert image.license_id == 1cies documents."""
    pipeline = DataPipeline(integration_config)
    def test_handle_invalid_values(self, csv_config, tmp_path):
        """Test handling of invalid values in CSV."""
        # Create test CSV with invalid values
        invalid_data = """id,content_type,copyright_holder,license_id,ok_for_export,diagnostic,width,height
82070,invalid,Chris Parrish,1,invalid,2,-100,-200
82071,image/jpeg,John Smith,1,1,0,0,0"""
        if pipeline.db:
        invalid_file = tmp_path / "invalid.csv"
        invalid_file.write_text(invalid_data)ollection("species").find_one(
                {"scientific_name": "Amanita muscaria"}
        processor = CSVProcessor(csv_config)
        df = next(processor.read_chunks(invalid_file))
            # Verify base fields
        # Test handling of invalid record
        invalid_record = df.iloc[0].to_dict() == "Amanita muscaria"
        with pytest.raises(ValidationError):hor 1"
            ImageSchema.model_validate(invalid_record)

        # Test handling of valid record
        valid_record = df.iloc[1].to_dict()s
        clean_record = { = species["descriptions"]
            "image_id": valid_record["id"],== "Red cap with white spots"
            "content_type": valid_record["content_type"],ifers", "Mixed woods"]
            "copyright_holder": valid_record["copyright_holder"],
            "license_id": valid_record["license_id"],
            "ok_for_export": bool(int(valid_record["ok_for_export"])),
            "diagnostic": bool(int(valid_record["diagnostic"])),taceae"
        }   assert species["classification"]["taxonomic_completeness"] == 1.0
        image = ImageSchema.model_validate(clean_record)
        assert image.content_type == "image/jpeg"
            assert "observations" in species
    @pytest.mark.parametrize(ecies.get("observations", {})
        "content_type,expected_valid",vation_count"] == 2
        [   assert len(observations["observations"]) == 2
            ("image/jpeg", True),
            ("image/png", True),ta
            ("image/gif", True),a" in species
            ("application/pdf", False),on_data"]
            ("text/plain", False),> 0
            ("invalid", False),e"] == "Test Forest" for loc in locations)
        ],
    )       # Verify image data
    def test_content_type_validation(self, csv_config, content_type, expected_valid):
        """Test validation of image content types."""
        record = { len(images) > 0
            "image_id": 1,["diagnostic"] is True for img in images)
            "content_type": content_type,
            "copyright_holder": "Test User",
            "license_id": 1,
        }   await pipeline.db.close()

        if expected_valid:
            image = ImageSchema.model_validate(record)
            assert image.content_type == content_typeon_config, integration_files):
        else:ggregation of species synonyms."""
            with pytest.raises(ValidationError):
                ImageSchema.model_validate(record)
        [
            {
                "id": 3,
                "text_name": "Synonym Name",
                "author": "Author 3",
                "deprecated": True,
                "rank": 4,
                "synonym_id": 1,  # Points to Amanita muscaria
            }
        ]
    )
    synonym_data.to_csv(
        integration_files / "synonyms.csv", index=False, mode="a", sep="\t"
    )

    pipeline = DataPipeline(integration_config)

    try:
        await pipeline.create_species_documents()

        if pipeline.db:
            species = await pipeline.db.get_collection("species").find_one(
                {"scientific_name": "Amanita muscaria"}
            )

            assert "synonyms" in species
            synonyms = species["synonyms"]
            assert len(synonyms) > 0
            assert any(syn["name"] == "Synonym Name" for syn in synonyms)

    finally:
        if pipeline.db:
            await pipeline.db.close()


@pytest.mark.asyncio
async def test_description_aggregation(integration_config, integration_files):
    """Test aggregation of multiple descriptions."""
    pipeline = DataPipeline(integration_config)

    try:
        # Add another description
        additional_desc = pd.DataFrame(
            [
                {
                    "id": 3,
                    "name_id": 1,
                    "source_type": 2,
                    "source_name": "Another Source",
                    "general_description": "Third description",
                    "habitat": "New habitat info",
                }
            ]
        )
        additional_desc.to_csv(
            integration_files / "name_descriptions.csv", index=False, mode="a", sep="\t"
        )

        await pipeline.create_species_documents()

        if pipeline.db:
            species = await pipeline.db.get_collection("species").find_one(
                {"scientific_name": "Amanita muscaria"}
            )

            descriptions = species["descriptions"]
            assert "sources" in descriptions
            assert len(descriptions["sources"]) >= 2  # Should have multiple sources

            # Check content aggregation
            assert descriptions["general"].startswith(
                "Red cap"
            )  # Original high-quality description
            assert "habitat" in descriptions  # Should include habitat information

    finally:
        if pipeline.db:
            await pipeline.db.close()


@pytest.mark.asyncio
async def test_observation_enrichment(integration_config, integration_files):
    """Test enrichment of species with observation data."""
    pipeline = DataPipeline(integration_config)

    try:
        await pipeline.create_species_documents()

        if pipeline.db:
            species = await pipeline.db.get_collection("species").find_one(
                {"scientific_name": "Amanita muscaria"}
            )

            observations = species["observations"]
            assert observations["observation_count"] == 2

            # Check observation statistics
            assert "vote_stats" in observations
            vote_stats = observations["vote_stats"]
            assert vote_stats["min"] == 1.5
            assert vote_stats["max"] == 2.5

            # Check location information in observations
            obs_list = observations["observations"]
            assert len(obs_list) == 2
            assert any(obs["location_name"] == "Test Forest" for obs in obs_list)

    finally:
        if pipeline.db:
            await pipeline.db.close()


@pytest.mark.asyncio
async def test_location_enrichment(integration_config, integration_files):
    """Test enrichment of species with location data."""
    pipeline = DataPipeline(integration_config)

    try:
        await pipeline.create_species_documents()

        if pipeline.db:
            species = await pipeline.db.get_collection("species").find_one(
                {"scientific_name": "Amanita muscaria"}
            )

            locations = species["location_data"]
            assert len(locations) == 2

            # Check location details
            forest_location = next(
                loc for loc in locations if loc["name"] == "Test Forest"
            )
            assert forest_location["elevation"] == "100-200m"
            assert forest_location["continent"] == "North America"
            assert "ecology" in forest_location
            assert forest_location["ecology"] == "Temperate rainforest"

    finally:
        if pipeline.db:
            await pipeline.db.close()


@pytest.mark.asyncio
async def test_image_enrichment(integration_config, integration_files):
    """Test enrichment of species with image data."""
    pipeline = DataPipeline(integration_config)

    try:
        await pipeline.create_species_documents()

        if pipeline.db:
            species = await pipeline.db.get_collection("species").find_one(
                {"scientific_name": "Amanita muscaria"}
            )

            images = species["images"]
            assert len(images) == 2

            # Check image metadata
            diagnostic_image = next(img for img in images if img["diagnostic"])
            assert diagnostic_image["content_type"] == "image/jpeg"
            assert diagnostic_image["width"] == 800
            assert diagnostic_image["height"] == 600

            # Check all images have required fields
            for image in images:
                assert "image_id" in image
                assert "content_type" in image
                assert "copyright_holder" in image
                assert "license_id" in image
                assert "rank" in image

    finally:
        if pipeline.db:
            await pipeline.db.close()


@pytest.mark.asyncio
async def test_incremental_enrichment(integration_config, integration_files):
    """Test incremental enrichment of species documents."""
    pipeline = DataPipeline(integration_config)

    try:
        # First create basic species documents
        await pipeline.process_csv_file(integration_files / "names.csv", "names")

        if pipeline.db:
            # Check basic document
            species = await pipeline.db.get_collection("species").find_one(
                {"scientific_name": "Amanita muscaria"}
            )
            assert species is not None
            assert "classification" not in species

            # Add classification data
            await pipeline.process_csv_file(
                integration_files / "name_classifications.csv", "name_classifications"
            )

            # Verify classification was added
            species = await pipeline.db.get_collection("species").find_one(
                {"scientific_name": "Amanita muscaria"}
            )
            assert "classification" in species
            assert species["classification"]["genus"] == "Amanita"

            # Add observation data
            await pipeline.process_csv_file(
                integration_files / "observations.csv", "observations"
            )

            # Verify observations were added
            species = await pipeline.db.get_collection("species").find_one(
                {"scientific_name": "Amanita muscaria"}
            )
            assert "observations" in species
            assert species["observations"]["observation_count"] > 0

    finally:
        if pipeline.db:
            await pipeline.db.close()
