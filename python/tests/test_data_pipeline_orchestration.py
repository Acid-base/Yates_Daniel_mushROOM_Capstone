"""Comprehensive Tests for CSV Data Processing and Integration."""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Any, List
from pydantic import ValidationErroreline
from src.config import DataConfig
from src.data_pipeline import (
    # your imports here
)
from src.data_csv import CSVProcessor
from src.schemas import ImageSchemaConfig(
path),
class TestCSVIntegrationPipeline:7",
    """Test class for CSV integration pipeline."""e",

@pytest.fixtureaN", "None"),
def csv_config(tmp_path):
    """Create a test configuration."""
    return DataConfig(
        DATA_DIR=str(tmp_path),
        MONGODB_URI="mongodb://localhost:27017",files(tmp_path):
        DATABASE_NAME="test_mushroom_csv",
        BATCH_SIZE=100,a
        NULL_VALUES=("", "NA", "N/A", "NULL", "NaN", "None"),(
    )

@pytest.fixture
def sample_observations_df():": "Amanita muscaria",
    """Create sample observations DataFrame.""": "Author 1",
    data = pd.DataFrame( False,
        [
            {
                "id": 1,
                "name_id": 1,
                "when": "2023-01-01",: "Boletus edulis",
                "location_id": 1,2",
                "lat": 45.5,
                "lng": -122.5,rank": 4,
                "alt": 100,
                "vote_cache": 1.5,
                "is_collection_location": True,
            },es.csv", index=False, sep="\t")
            {
                "id": 2,
                "name_id": 2,DataFrame(
                "when": "2023-01-02",
                "location_id": 2,
                "lat": 46.5,
                "lng": -123.5,Fungi",
                "alt": 200,
                "vote_cache": 2.5,
                "is_collection_location": False,",
            },family": "Amanitaceae",
        ]   "genus": "Amanita",
    )
    return data

@pytest.fixture
def sample_names_df():
    """Create sample names DataFrame."""   "class": "Agaricomycetes",
    data = pd.DataFrame(les",
        [
            {
                "id": 1,
                "text_name": "Amanita muscaria",
                "author": "Author 1",
                "deprecated": False,
                "rank": 4,False, sep="\t"
            },
            {
                "id": 2,    # Observations data
                "text_name": "Boletus edulis",
                "author": "Author 2",
                "deprecated": False,
                "rank": 4,                "id": 1,
            },
        ]
    )
    return data
                "lng": -122.5,
async def run_data_pipeline(config: DataConfig, input_files: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """Run the data pipeline with provided configuration and input files."""
    pipeline = DataPipeline(config)lection_location": True,

    # Process each input file            {
    for filename, data in input_files.items():
        file_path = Path(config.DATA_DIR) / filename                "name_id": 2,
        pd.DataFrame(data).to_csv(file_path, index=False)                "when": "2023-01-02",

        table_name = filename.replace(".csv", "")                "lat": 46.5,
        success = await pipeline.process_csv_file(file_path, table_name)   "lng": -123.5,
        if not success:                "alt": 200,
            raise RuntimeError(f"Failed to process {filename}")
False,
    return pipeline.data_storage
        ]
    )
"""Integration tests for the full data pipeline flow (using real CSV processing)."""ndex=False, sep="\t")

import pytest

# Import DataPipeline, DataConfig, and CSV processing functions (replace with your actual imports)
from src.data_pipeline import DataPipeline
from src.config import DataConfigline_config):
"
eline(pipeline_config)
# --- Fixtures (Reusing and adapting from previous tests) ---ig
@pytest.fixture
def csv_config_integration(tmp_path):  # Specific config for integration testsone
    """Fixture for DataConfig for integration tests, creates test data directory."""ors == []
    test_data_dir = (
        tmp_path / "test_integration_data"
    )  # Separate dir for integration tests@pytest.mark.asyncio
    test_data_dir.mkdir(exist_ok=True)async def test_full_pipeline_execution(pipeline_config, test_files):
    return DataConfig(l pipeline execution with all data types."""
        MONGODB_URI="mongodb://test:27017",
        DATABASE_NAME="test_integration_db",  # Separate DB for integration tests
        DATA_DIR=test_data_dir,
        BATCH_SIZE=100,eline
        CHUNK_SIZE=1024,ync()
    )success is True

# Verify progress
@pytest.fixturetotal > 0
def pipeline_integration(csv_config_integration):ssert pipeline.progress.processed > 0
    """Fixture to create DataPipeline instance for integration tests."""
    return DataPipeline(assert pipeline.progress.errors == 0
        csv_config_integration
    )  # No cleanup needed for this test example        # Verify species documents were created
    look_alikes if pipeline.db:
    Agaricus campestris, Agaricus bitorquis.      species_collection = pipeline.db.get_collection("species")
    uses       count = await species_collection.count_documents({})
    Edible and widely cultivated. assert count == 2  # We created 2 species in test data
    notes
    Some interesting notes about Agaricus bisporus.heck enriched data
    refs       species = await species_collection.find_one(
    http://mushroomexpert.com/agaricus_bisporus.html {"scientific_name": "Amanita muscaria"}

    ---assert species is not None
    idet("genus") == "Amanita"
    3ssert len(species.get("observations", [])) > 0
    name_id
    3:
    source_typedb:
    1it pipeline.db.close()
    source_name
    System Aggregate
    gen_desc
    General description for Agaricus campestris group. test_pipeline_error_handling(pipeline_config, test_files):
    diag_descalid data."""
    Group diagnostic description.eate invalid data file
    habitatalid", "name": None}])
    Meadows, fields.alid_data.to_csv(test_files / "invalid.csv", index=False)
    look_alikes
    Multiple Agaricus species.
    uses
    Edible, some caution advised.
    notes
    Notes for the Agaricus campestris group.")
    refs
    Reference for Agaricus campestris group.
    """

    NAME_CLASSIFICATIONS_CSV_TEST_DATA = """id\tname_id\tdomain\tkingdom\tphylum\tclass\torder\tfamily
    1\t1\tEukaryota\tFungi\t\t\t\t
    2\t2\tEukaryota\tFungi\tBasidiomycota\tAgaricomycetes\tAgaricales\tAgaricaceae
    3\t3\tEukaryota\tFungi\tBasidiomycota\tAgaricomycetes\tAgaricales\tAgaricaceae
    4\t4\tEukaryota\tFungi\tBasidiomycota\tAgaricomycetes\tAgaricales\tAgaricaceae
    5\t5\tEukaryota\tFungi\tBasidiomycota\tAgaricomycetes\tAgaricales\tAgaricaceaeef test_pipeline_data_transformations(pipeline_config, test_files):
    6\t6\tEukaryota\tFungi\tBasidiomycota\tAgaricomycetes\tAgaricales\tBoletaceae    """Test data transformations during pipeline processing."""
    7\t7\tEukaryota\tFungi\tBasidiomycota\tAgaricomycetes\tBoletales\tBoletaceae
    8\t8\tEukaryota\tFungi\tBasidiomycota\tAgaricomycetes\tAgaricales\tCantharellaceae
    9\t9\tEukaryota\tFungi\tBasidiomycota\tAgaricomycetes\tAgaricales\tAmanitaceaey:
    10\t10\tEukaryota\tFungi\tBasidiomycota\tAgaricomycetes\tAgaricales\tAmanitaceae
    11\t11\tEukaryota\tFungi\tAscomycota\tSordariomycetes\tXylariales\tClavariaceae(
    12\t12\tEukaryota\tFungi\tBasidiomycota\tAgaricomycetes\tGomphales\tClavariadelphaceae
    13\t13\tEukaryota\tPlantae\tTracheophyta\tMagnoliopsida\tRosales\tRosaceae        )
    """

    def test_data_pipeline_integration_real_csv(            # Verify transformations
        self, pipeline_integration, setup_integration_csv_filesspecies").find_one(
    ):
        """Tests the data pipeline end-to-end with real CSV processing (integration test)."""
        config = csv_config_integration
        output_json_list = run_data_pipeline(config)  # Run the data pipeline   assert (
                species["classification"]["taxonomic_completeness"] == 1.0
        # --- Assertions - Similar to test_csv_integration.py, but now testing full pipeline ---
        # 1. Check if pipeline ran without errors (implicitly checked if no exceptions are raised)

        # 2. Check if output is a list of JSON documentsf pipeline.db:
        assert isinstance(output_json_list, list), "Output should be a list"            await pipeline.db.close()
        assert all(isinstance(doc, dict) for doc in output_json_list), (
            "Each item in output should be a dict (JSON document)"
        )
iles):
        # 3. Check if output is not empty (at least some species processed from test data)resume processing."""
        assert output_json_list, (peline(pipeline_config)
            "Output JSON list should not be empty - no species processed"
        )
 Process first file
        # 4. Find Agaricus bisporus document and validate its content        await pipeline.process_csv_file(test_files / "names.csv", "names")
        agaricus_doc = None
        for doc in output_json_list:
            if doc.get("scientific_name") == "Agaricus bisporus":imulating restart)
                agaricus_doc = docline = DataPipeline(pipeline_config)
                break
        assert agaricus_doc is not None, (off
            "Agaricus bisporus document not found in output"wait new_pipeline.process_csv_file(
        )ns"

        # 5. Validate Agaricus bisporus document content (more comprehensive assertions needed here!)
        assert agaricus_doc["scientific_name"] == "Agaricus bisporus"        assert new_pipeline.progress.processed > initial_progress
        assert agaricus_doc["rank"] == 20
        assert (
            "Detailed general description for Agaricus bisporus"
            in agaricus_doc["description"]["general"]
        )f new_pipeline.db:
        assert "Agaricaceae" in agaricus_doc["classification"]["family"]t new_pipeline.db.close()
        # --- ADD MORE DETAILED ASSERTIONS HERE to validate more fields, aggregated data, data types, etc.
        # --- Based on your expected output structure and transformations defined in the wrangling report.

        # 6. Check for absence of 'group' and 'deprecated' species in output
        species_names_in_output = [doc["scientific_name"] for doc in output_json_list]ata validation during pipeline processing."""
        assert "Agaricus campestris group" not in species_names_in_output, (
            "'group' names should be filtered out"
        )    try:
        assert (
            "Agaricus sylvaticus" not in species_names_in_output
            or "Agaricus sylvaticus"
            not in [
                doc["scientific_name"] for doc in output_json_list if doc["id"] == 5
            ]
        ), "'deprecated' names should be filtered out"

        ]
# --- Further improvements for test_data_pipeline_integration.py ---
# 1. **Crucially: Add more comprehensive assertions in `test_data_pipeline_integration_real_csv` to validate the *content* of the output JSON documents.**
#    Check more fields, nested structures (description, classification, images, observation_summary if included), aggregated data, data types, etc.        success = await pipeline.store_species_batch(species_data)
#    Reference your `FieldGuideSpeciesDocument` schema and the expected transformations from the wrangling report.t success is True
# 2. **Expand the test data (in `setup_integration_csv_files` and the `NAMES_CSV_TEST_DATA` etc. strings) to include data for *all* CSV files**, not just names, name_descriptions, and name_classifications.
#    This will allow you to test the integration of the entire pipeline and all data sources.        if pipeline.db:
# 3. **Test data variations and edge cases in the integration tests.**  Include data that tests error handling and data cleaning logic at the pipeline level.
# 4. **Consider adding tests for API enrichment and database interaction within the integration tests** if you want to verify those aspects in a more integrated way (though mocking might still be preferred for speed and isolation in most integration tests, reserving real API/DB tests for separate E2E tests).            count = await pipeline.db.get_collection("species").count_documents({})
            assert count == 1

"""Optional: End-to-End tests for the full data pipeline with real/mock API and database."""

import pytest
# You might need libraries for mocking API calls (e.g., httpx mock, requests-mock) and a test MongoDB instance

# Import DataPipeline and DataConfig (replace with your actual imports)


# --- Fixtures (Adjust as needed for E2E tests - might need real/mock DB and API setup) ---eline_config)
@pytest.fixture
def csv_config_e2e(tmp_path):
    """Fixture for DataConfig for end-to-end tests."""
    test_data_dir = tmp_path / "test_e2e_data"   tasks = [
    test_data_dir.mkdir(exist_ok=True)            pipeline.process_csv_file(test_files / "names.csv", "names"),
    return DataConfig(  # Adjust DataConfig for E2E - potentially using a test MongoDB URI            pipeline.process_csv_file(test_files / "observations.csv", "observations"),
        MONGODB_URI="mongodb://test:27017",  #  <- Replace with a test MongoDB URI or mock setupeline.process_csv_file(
        DATABASE_NAME="test_e2e_db",  # Separate DB for E2E testssifications.csv", "name_classifications"
        DATA_DIR=test_data_dir,
        BATCH_SIZE=100,
        CHUNK_SIZE=1024,
        # ... potentially other config settings for E2E tests ...await asyncio.gather(*tasks)
    )d succeed

        # Verify all data was processed
@pytest.fixtureline.db:
async def pipeline_e2e(csv_config_e2e):
    """Fixture to create DataPipeline instance for end-to-end tests."""
    # Potentially set up a test MongoDB instance here (e.g., using Docker, or an in-memory DB)
    pipeline = DataPipeline(csv_config_e2e)
    yield pipeline            )
    await pipeline.cleanup()  # Cleanup test DB if needed
       assert any(s.get("classification") for s in species)
observations") for s in species)
@pytest.fixture
def setup_e2e_csv_files(csv_config_e2e):
    """Fixture to create simulated CSV files for end-to-end tests."""
    data_dir = csv_config_e2e.DATA_DIR        await pipeline.db.close()
    # Create CSV files in data_dir - similar to setup_integration_csv_files, but potentially with more comprehensive data

    # Example - create names.csv (adjust content as needed for E2E tests)@pytest.mark.asyncio
    (async def test_pipeline_memory_management(pipeline_config, test_files):
        data_dir / "names.csv"."""
    ).write_text("""id\ttext_name\tauthor\tdeprecated\tcorrect_spelling_id\tsynonym_id\trankine(pipeline_config)
1\tFungi\t\t0\t\t\t1
2\tAgaricus bisporus\t(J.E. Lange) Imbach\t0\t\t\t20
""") chunks
    # ... Create other CSV files as needed for E2E tests ...
    return data_dir            [
pecies {i}", "rank": 4}
0,000 records
class TestDataPipelineE2E:  # Class for end-to-end tests            ]
    @pytest.mark.asyncio
    async def test_data_pipeline_e2e_full_flow(self, pipeline_e2e, setup_e2e_csv_files):        large_data.to_csv(test_files / "large_names.csv", index=False)
        """Tests the complete end-to-end data pipeline flow, including API and database interaction."""
        config = csv_config_e2e        # Process should complete without memory issues
        output_json_list = run_data_pipeline(config)  # Run the data pipeline

        # --- Assertions for E2E tests ---
        # 1. Check if pipeline ran without errors

        # 2. Check if output is a list of JSON documents
species").count_documents({})
        # 3. Check if output is not empty

        # 4. Validate data in MongoDB (query the test MongoDB database directly using pipeline.db client)
        #    Example (adjust based on your MongoDB access and expected data):
        #    db_client = pipeline_e2e.db.clientse()
        #    collection = db_client[config.DATABASE_NAME]["your_collection_name"]
        #    agaricus_doc_from_db = await collection.find_one({"scientific_name": "Agaricus bisporus"})
        #    assert agaricus_doc_from_db is not None
        #    assert agaricus_doc_from_db["rank"] == 20t_pipeline_progress_tracking(pipeline_config, test_files):
        #    # ... Add more assertions to validate data in the database against expected output ...e progress tracking."""
    pipeline = DataPipeline(pipeline_config)
        # 5. Validate API interactions (if you are mocking or recording API calls in E2E tests)
        #    Example (if using httpx mock):
        #    with httpx_mock.mock        # Process files and check progress
        for file_name in ["names.csv", "observations.csv", "name_classifications.csv"]:
ore_count = pipeline.progress.processed
"""Tests for data pipeline integration phase."""s_csv_file(
import pytest")[0]
import pandas as pd
ine.progress.processed
from config import DataConfig
from data_pipeline import DataPipelinerogress should increase


@pytest.fixture   assert pipeline.progress.total > 0
def integration_config(tmp_path):        assert pipeline.progress.processed == pipeline.progress.total
    """Create test configuration for integration tests."""        assert pipeline.progress.errors == 0
    return DataConfig(
        DATA_DIR=str(tmp_path),
        MONGODB_URI="mongodb://localhost:27017",
        DATABASE_NAME="test_mushroom_integration",.close()
        BATCH_SIZE=100,        NULL_VALUES=("", "NA", "N/A", "NULL", "NaN", "None"),    )@pytest.fixturedef integration_files(tmp_path):    """Create test files for integration testing."""    # Names with descriptions    names_data = pd.DataFrame(        [            {                "id": 1,                "text_name": "Amanita muscaria",                "author": "Author 1",                "deprecated": False,                "rank": 4,            },            {                "id": 2,                "text_name": "Boletus edulis",                "author": "Author 2",                "deprecated": False,                "rank": 4,            },        ]    )    names_data.to_csv(tmp_path / "names.csv", index=False, sep="\t")    descriptions_data = pd.DataFrame(        [            {                "id": 1,                "name_id": 1,                "source_type": 0,                "source_name": "System",                "general_description": "Red cap with white spots",                "diagnostic_description": "Distinctive red cap",                "distribution": "Widespread",                "habitat": "Under conifers",                "look_alikes": "None known",                "uses": "Medicinal",                "notes": "Iconic mushroom",            },            {                "id": 2,                "name_id": 1,                "source_type": 1,                "source_name": "User",                "general_description": "Additional description",                "habitat": "Mixed woods",            },        ]    )    descriptions_data.to_csv(tmp_path / "name_descriptions.csv", index=False, sep="\t")    # Classifications    classifications_data = pd.DataFrame(        [            {                "name_id": 1,                "kingdom": "Fungi",                "phylum": "Basidiomycota",                "class": "Agaricomycetes",                "order": "Agaricales",                "family": "Amanitaceae",                "genus": "Amanita",            },            {                "name_id": 2,                "kingdom": "Fungi",                "phylum": "Basidiomycota",                "class": "Agaricomycetes",                "order": "Boletales",                "family": "Boletaceae",                "genus": "Boletus",            },        ]    )    classifications_data.to_csv(        tmp_path / "name_classifications.csv", index=False, sep="\t"    )    # Locations and descriptions    locations_data = pd.DataFrame(        [            {                "id": 1,                "name": "Test Forest",                "north": 45.5,                "south": 45.4,                "east": -122.5,                "west": -122.6,                "elevation": "100-200",                "continent": "North America",            },            {                "id": 2,                "name": "Test Mountain",                "north": 46.5,                "south": 46.4,                "east": -121.5,                "west": -121.6,                "elevation": "1000-2000",                "continent": "North America",            },        ]    )    locations_data.to_csv(tmp_path / "locations.csv", index=False, sep="\t")    location_descriptions_data = pd.DataFrame(        [            {                "id": 1,                "location_id": 1,                "source_type": 0,                "gen_desc": "Mixed forest area",                "ecology": "Temperate rainforest",                "species": "Various mushrooms present",            },            {                "id": 2,                "location_id": 2,                "source_type": 0,                "gen_desc": "Mountain habitat",                "ecology": "Alpine forest",                "species": "Various fungi",            },        ]    )    location_descriptions_data.to_csv(        tmp_path / "location_descriptions.csv", index=False, sep="\t"    )    # Observations    observations_data = pd.DataFrame(        [            {                "id": 1,                "name_id": 1,                "when": "2023-01-01",                "location_id": 1,                "lat": 45.5,                "lng": -122.5,                "alt": 150,                "vote_cache": 1.5,                "is_collection_location": True,            },            {                "id": 2,                "name_id": 1,                "when": "2023-01-02",                "location_id": 2,                "lat": 46.5,                "lng": -121.5,                "alt": 1500,                "vote_cache": 2.5,                "is_collection_location": True,            },        ]    )    observations_data.to_csv(tmp_path / "observations.csv", index=False, sep="\t")    # Images and image-observation links    images_data = pd.DataFrame(        [            {                "id": 1,                "content_type": "image/jpeg",                "copyright_holder": "User 1",                "license_id": 1,                "ok_for_export": True,                "diagnostic": True,                "width": 800,                "height": 600,            },            {                "id": 2,                "content_type": "image/jpeg",                "copyright_holder": "User 2",                "license_id": 1,                "ok_for_export": True,                "diagnostic": False,                "width": 1024,                "height": 768,            },        ]    )    images_data.to_csv(tmp_path / "images.csv", index=False, sep="\t")    images_observations_data = pd.DataFrame(        [            {"image_id": 1, "observation_id": 1, "rank": 1},            {"image_id": 2, "observation_id": 2, "rank": 2},        ]    )    images_observations_data.to_csv(        tmp_path / "images_observations.csv", index=False, sep="\t"    )    return tmp_path@pytest.mark.asyncioasync def test_species_document_creation(integration_config, integration_files):    """Test creation of complete species documents."""    pipeline = DataPipeline(integration_config)    try:        # Run create_species_documents        success = await pipeline.create_species_documents()        assert success is True        if pipeline.db:            # Get created species document            species = await pipeline.db.get_collection("species").find_one(                {"scientific_name": "Amanita muscaria"}            )            # Verify base fields            assert species is not None            assert species["scientific_name"] == "Amanita muscaria"            assert species["author"] == "Author 1"            assert species["rank"] == 4            # Verify descriptions            assert "descriptions" in species            descriptions = species["descriptions"]            assert descriptions["general"] == "Red cap with white spots"            assert descriptions["habitat"] in ["Under conifers", "Mixed woods"]            # Verify classification            assert species["classification"]["genus"] == "Amanita"            assert species["classification"]["family"] == "Amanitaceae"            assert species["classification"]["taxonomic_completeness"] == 1.0            # Verify observations            assert "observations" in species            observations = species.get("observations", {})            assert observations["observation_count"] == 2            assert len(observations["observations"]) == 2            # Verify location data            assert "location_data" in species            locations = species["location_data"]            assert len(locations) > 0            assert any(loc["name"] == "Test Forest" for loc in locations)            # Verify image data            assert "images" in species            images = species["images"]            assert len(images) > 0            assert any(img["diagnostic"] is True for img in images)    finally:        if pipeline.db:            await pipeline.db.close()@pytest.mark.asyncioasync def test_species_synonyms_aggregation(integration_config, integration_files):    """Test aggregation of species synonyms."""    # Add synonym relationships to names data    synonym_data = pd.DataFrame(        [            {                "id": 3,                "text_name": "Synonym Name",                "author": "Author 3",                "deprecated": True,                "rank": 4,                "synonym_id": 1,  # Points to Amanita muscaria            }        ]    )    synonym_data.to_csv(        integration_files / "synonyms.csv", index=False, mode="a", sep="\t"    )    pipeline = DataPipeline(integration_config)    try:        await pipeline.create_species_documents()        if pipeline.db:            species = await pipeline.db.get_collection("species").find_one(                {"scientific_name": "Amanita muscaria"}            )            assert "synonyms" in species            synonyms = species["synonyms"]            assert len(synonyms) > 0            assert any(syn["name"] == "Synonym Name" for syn in synonyms)    finally:        if pipeline.db:            await pipeline.db.close()@pytest.mark.asyncioasync def test_description_aggregation(integration_config, integration_files):    """Test aggregation of multiple descriptions."""    pipeline = DataPipeline(integration_config)    try:        # Add another description        additional_desc = pd.DataFrame(            [                {                    "id": 3,                    "name_id": 1,                    "source_type": 2,                    "source_name": "Another Source",                    "general_description": "Third description",                    "habitat": "New habitat info",                }            ]        )        additional_desc.to_csv(            integration_files / "name_descriptions.csv", index=False, mode="a", sep="\t"        )        await pipeline.create_species_documents()        if pipeline.db:            species = await pipeline.db.get_collection("species").find_one(                {"scientific_name": "Amanita muscaria"}            )            descriptions = species["descriptions"]            assert "sources" in descriptions            assert len(descriptions["sources"]) >= 2  # Should have multiple sources            # Check content aggregation            assert descriptions["general"].startswith(                "Red cap"            )  # Original high-quality description            assert "habitat" in descriptions  # Should include habitat information    finally:        if pipeline.db:            await pipeline.db.close()@pytest.mark.asyncioasync def test_observation_enrichment(integration_config, integration_files):    """Test enrichment of species with observation data."""    pipeline = DataPipeline(integration_config)    try:        await pipeline.create_species_documents()        if pipeline.db:            species = await pipeline.db.get_collection("species").find_one(                {"scientific_name": "Amanita muscaria"}            )            observations = species["observations"]            assert observations["observation_count"] == 2            # Check observation statistics            assert "vote_stats" in observations            vote_stats = observations["vote_stats"]            assert vote_stats["min"] == 1.5            assert vote_stats["max"] == 2.5            # Check location information in observations            obs_list = observations["observations"]            assert len(obs_list) == 2            assert any(obs["location_name"] == "Test Forest" for obs in obs_list)    finally:        if pipeline.db:            await pipeline.db.close()@pytest.mark.asyncioasync def test_location_enrichment(integration_config, integration_files):    """Test enrichment of species with location data."""    pipeline = DataPipeline(integration_config)    try:        await pipeline.create_species_documents()        if pipeline.db:            species = await pipeline.db.get_collection("species").find_one(                {"scientific_name": "Amanita muscaria"}            )            locations = species["location_data"]            assert len(locations) == 2            # Check location details            forest_location = next(                loc for loc in locations if loc["name"] == "Test Forest"            )            assert forest_location["elevation"] == "100-200m"            assert forest_location["continent"] == "North America"            assert "ecology" in forest_location            assert forest_location["ecology"] == "Temperate rainforest"    finally:        if pipeline.db:            await pipeline.db.close()@pytest.mark.asyncioasync def test_image_enrichment(integration_config, integration_files):    """Test enrichment of species with image data."""    pipeline = DataPipeline(integration_config)    try:        await pipeline.create_species_documents()        if pipeline.db:            species = await pipeline.db.get_collection("species").find_one(                {"scientific_name": "Amanita muscaria"}            )            images = species["images"]            assert len(images) == 2            # Check image metadata            diagnostic_image = next(img for img in images if img["diagnostic"])            assert diagnostic_image["content_type"] == "image/jpeg"            assert diagnostic_image["width"] == 800            assert diagnostic_image["height"] == 600            # Check all images have required fields            for image in images:                assert "image_id" in image                assert "content_type" in image                assert "copyright_holder" in image                assert "license_id" in image                assert "rank" in image    finally:        if pipeline.db:            await pipeline.db.close()@pytest.mark.asyncioasync def test_incremental_enrichment(integration_config, integration_files):    """Test incremental enrichment of species documents."""    pipeline = DataPipeline(integration_config)    try:        # First create basic species documents        await pipeline.process_csv_file(integration_files / "names.csv", "names")        if pipeline.db:            # Check basic document            species = await pipeline.db.get_collection("species").find_one(                {"scientific_name": "Amanita muscaria"}            )            assert species is not None            assert "classification" not in species            # Add classification data            await pipeline.process_csv_file(                integration_files / "name_classifications.csv", "name_classifications"            )            # Verify classification was added            species = await pipeline.db.get_collection("species").find_one(                {"scientific_name": "Amanita muscaria"}            )            assert "classification" in species            assert species["classification"]["genus"] == "Amanita"            # Add observation data            await pipeline.process_csv_file(                integration_files / "observations.csv", "observations"            )            # Verify observations were added            species = await pipeline.db.get_collection("species").find_one(
                {"scientific_name": "Amanita muscaria"}
            )
            assert "observations" in species
            assert species["observations"]["observation_count"] > 0

    finally:
        if pipeline.db:
            await pipeline.db.close()
