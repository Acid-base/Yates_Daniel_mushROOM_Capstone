from datetime import datetime
from typing import Dict, List, Any
import pytest
from ..data_csv import (
    safe_cast,
    clean_text,
    parse_date,
    process_names,
    validate_taxonomy,
    BoundingBox,
    ImageMetadata,
    License,
    determine_location_type,
    parse_location_hierarchy,
    DataConfig,
    process_images,
    process_image_observations,
    process_location_descriptions,
    process_locations,
    process_name_classifications,
    process_name_descriptions,
    process_observations,
)


# Fixtures
@pytest.fixture
def sample_names() -> List[Dict[str, Any]]:
    return [
        {
            "id": "1",
            "text_name": "Species one",
            "author": "Author 1",
            "deprecated": "0",
            "correct_spelling_id": "",
            "rank": "1",
        },
        {
            "id": "2",
            "text_name": "Species two",
            "author": "Author 2",
            "deprecated": "1",
            "correct_spelling_id": "1",
            "rank": "1",
        },
    ]


@pytest.fixture
def sample_taxonomy() -> Dict[str, str]:
    return {
        "domain": "Eukarya",
        "kingdom": "Fungi",
        "phylum": "Ascomycota",
        "class": "Lecanoromycetes",
        "order": "Lecanorales",
        "family": "Parmeliaceae",
    }


# Test utility functions
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
def test_safe_cast(input_value, type_cast, expected):
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
def test_clean_text(input_text, expected):
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
def test_parse_date(date_string, expected):
    assert parse_date(date_string) == expected


def test_process_names(sample_names):
    result = process_names(sample_names)

    expected_keys = {"text_name", "deprecated", "correct_spelling_id", "misspellings"}
    assert all(key in result[1] for key in expected_keys)
    assert all(key in result[2] for key in expected_keys)

    # Verify specific fields rather than entire structure
    assert result[1]["text_name"] == "Species one"
    assert result[1]["deprecated"] is False
    assert result[1]["correct_spelling_id"] is None
    assert 2 in result[1]["misspellings"]

    assert result[2]["text_name"] == "Species two"
    assert result[2]["deprecated"] is True
    assert result[2]["correct_spelling_id"] == 1
    assert len(result[2]["misspellings"]) == 0


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
def test_validate_taxonomy(taxonomy_data, expected_error):
    errors = validate_taxonomy(taxonomy_data)
    if expected_error:
        assert expected_error in errors
    else:
        assert not errors


# Test dataclass functionality
def test_bounding_box():
    bbox = BoundingBox(
        north=45.0, south=44.0, east=-122.0, west=-123.0, high=1000.0, low=0.0
    )

    assert bbox.center == (44.5, -122.5)
    assert bbox.dimensions == (1.0, 1.0)
    assert bbox.elevation_range == (0.0, 1000.0)


def test_image_metadata():
    metadata = ImageMetadata(
        _id=1,
        url="https://example.com/image.jpg",
        license=License.CC_BY,
        copyright_holder="Test User",
        date=datetime(2023, 1, 1),
        original_url="https://original.example.com/image.jpg",
        notes="Test notes",
        width=800,
        height=600,
        crop=BoundingBox(north=45.0, south=44.0, east=-122.0, west=-123.0),
        observation_id=123,
    )

    # Test that the object was created successfully
    assert metadata._id == 1
    assert metadata.url == "https://example.com/image.jpg"
    assert metadata.license == License.CC_BY
    assert metadata.copyright_holder == "Test User"
    assert metadata.date == datetime(2023, 1, 1)
    assert metadata.width == 800
    assert metadata.height == 600
    assert metadata.observation_id == 123

    # Test the crop bounding box
    assert metadata.crop.north == 45.0
    assert metadata.crop.south == 44.0
    assert metadata.crop.east == -122.0
    assert metadata.crop.west == -123.0


# Test location processing
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
def test_determine_location_type(name: str, expected_type: str):
    assert determine_location_type(name) == expected_type


def test_parse_location_hierarchy():
    location = "Mount Hood, Clackamas Co., Oregon, USA"
    hierarchy = parse_location_hierarchy(location)

    assert hierarchy["place"] == "Mount Hood"
    assert hierarchy["county"] == "Clackamas Co."
    assert hierarchy["state"] == "Oregon"
    assert hierarchy["country"] == "USA"


# Test configuration
def test_data_config():
    assert DataConfig.DEFAULT_DELIMITER == "\t"
    assert DataConfig.BATCH_SIZE == 1000
    assert DataConfig.DATE_FORMAT == "%Y-%m-%d"
    assert "NULL" in DataConfig.NULL_VALUES


# Integration tests
def test_process_names_integration(sample_names):
    # Test the full names processing pipeline
    processed = process_names(sample_names)

    # Verify structure and relationships
    assert all(isinstance(id_, int) for id_ in processed.keys())
    assert all("_id" in data for data in processed.values())
    assert all("synonyms" in data for data in processed.values())
    assert all("misspellings" in data for data in processed.values())


def test_process_image_observations():
    # Test data based on the first few rows of images_observations.csv
    test_data = [
        {"image_id": "1", "observation_id": "1"},
        {"image_id": "2", "observation_id": "2"},
        {"image_id": "3", "observation_id": "3"},
        {"image_id": "9", "observation_id": "9"},
        {
            "image_id": "10",
            "observation_id": "9",
        },  # Multiple images for one observation
        {"image_id": "21", "observation_id": "18"},
        {"image_id": "22", "observation_id": "18"},
        {"image_id": "23", "observation_id": "18"},
        {
            "image_id": "24",
            "observation_id": "18",
        },  # Multiple images for one observation
    ]

    result = process_image_observations(test_data)

    # Test basic mapping
    assert result[1] == [1]  # Observation 1 has image 1
    assert result[2] == [2]  # Observation 2 has image 2
    assert result[3] == [3]  # Observation 3 has image 3

    # Test multiple images for one observation
    assert result[9] == [9, 10]  # Observation 9 has images 9 and 10
    assert result[18] == [
        21,
        22,
        23,
        24,
    ]  # Observation 18 has images 21, 22, 23, and 24

    # Test non-existent observation
    assert 100 not in result  # Observation 100 doesn't exist

    # Test result structure
    assert isinstance(result, dict)
    assert all(isinstance(k, int) for k in result.keys())  # All keys should be integers
    assert all(
        isinstance(v, list) for v in result.values()
    )  # All values should be lists
    assert all(
        isinstance(i, int) for v in result.values() for i in v
    )  # All image IDs should be integers


def test_process_images():
    # Sample test data based on images.csv
    test_images = [
        {
            "id": "1",
            "content_type": "image/jpeg",
            "copyright_holder": "Nathan Wilson",
            "license": "Creative Commons Wikipedia Compatible v3.0",
            "ok_for_export": "1",
            "diagnostic": "1",
        },
        {
            "id": "2",
            "content_type": "image/jpeg",
            "copyright_holder": "Nathan Wilson",
            "license": "Creative Commons Wikipedia Compatible v3.0",
            "ok_for_export": "1",
            "diagnostic": "1",
        },
        {
            "id": "3",
            "content_type": "image/jpeg",
            "copyright_holder": "Nathan Wilson",
            "license": "Creative Commons Wikipedia Compatible v3.0",
            "ok_for_export": "1",
            "diagnostic": "1",
        },
    ]

    # Sample image-observation mapping
    image_obs_mapping = {
        1: [1],
        2: [2],
        3: [3, 4],  # One image linked to multiple observations
    }

    result = process_images(test_images, image_obs_mapping)

    # Test basic structure
    assert isinstance(result, dict)

    # Test first image
    assert result[1]["_id"] == 1
    assert result[1]["content_type"] == "image/jpeg"
    assert result[1]["copyright_holder"] == "Nathan Wilson"
    assert result[1]["license"] == "Creative Commons Wikipedia Compatible v3.0"
    assert result[1]["ok_for_export"] is True  # Should be converted to boolean
    assert result[1]["diagnostic"] is True  # Should be converted to boolean
    assert result[1]["observations"] == [1]  # Should contain linked observation IDs

    # Test image with multiple observations
    assert result[3]["observations"] == [3, 4]

    # Test data type conversions
    for img_id, img_data in result.items():
        assert isinstance(img_id, int)
        assert isinstance(img_data["_id"], int)
        assert isinstance(img_data["ok_for_export"], bool)
        assert isinstance(img_data["diagnostic"], bool)
        assert isinstance(img_data["observations"], list)

    # Test that all required fields are present
    required_fields = {
        "_id",
        "content_type",
        "copyright_holder",
        "license",
        "ok_for_export",
        "diagnostic",
        "observations",
    }
    for img_data in result.values():
        assert all(field in img_data for field in required_fields)

    # Test that non-existent images are not included
    assert 999 not in result

    # Test that all images from input are processed
    assert len(result) == len(test_images)


def test_process_location_descriptions():
    # Sample test data based on location_descriptions.csv
    test_data = [
        {
            "id": "1",
            "location_id": "3",
            "source_type": "1",
            "source_name": "NULL",
            "gen_desc": "NULL",
            "ecology": "NULL",
            "species": "NULL",
            "notes": "Location refined based on notes from Doug Smith.\n",
            "refs": "NULL",
        },
        {
            "id": "2",
            "location_id": "12",
            "source_type": "1",
            "source_name": "NULL",
            "gen_desc": "NULL",
            "ecology": "NULL",
            "species": "NULL",
            "notes": 'This is a gated community called "Buttonwood Bay Condominiums" at milepost 96...',
            "refs": "NULL",
        },
        {
            "id": "3",
            "location_id": "13",
            "source_type": "1",
            "source_name": "",
            "gen_desc": "This is a hammock located on south Key Largo...",
            "ecology": "The bay side is hammock blending rapidly into coastal buttonwood scrub...",
            "species": "Airplants (_Tillandsia_ spp.) and lichens...",
            "notes": "Rockland / dwarf mangrove forest near the old dump:",
            "refs": "",
        },
    ]

    result = process_location_descriptions(test_data)

    # Test basic structure
    assert isinstance(result, dict)

    # Test first location description
    loc1 = result[3]  # Using location_id as key
    assert loc1["_id"] == 1
    assert loc1["location_id"] == 3
    assert loc1["source_type"] == 1
    assert loc1["notes"] == "Location refined based on notes from Doug Smith."
    assert loc1["source_name"] is None
    assert loc1["gen_desc"] is None
    assert loc1["ecology"] is None
    assert loc1["species"] is None
    assert loc1["refs"] is None

    # Test location with full data
    loc3 = result[13]
    assert loc3["_id"] == 3
    assert loc3["location_id"] == 13
    assert loc3["source_type"] == 1
    assert loc3["gen_desc"].startswith("This is a hammock located")
    assert loc3["ecology"].startswith("The bay side is hammock")
    assert loc3["species"].startswith("Airplants")
    assert loc3["notes"].startswith("Rockland / dwarf mangrove")
    assert loc3["refs"] is None  # Empty string should be converted to None

    # Test data type conversions
    for loc_id, loc_data in result.items():
        assert isinstance(loc_id, int)
        assert isinstance(loc_data["_id"], int)
        assert isinstance(loc_data["location_id"], int)
        assert isinstance(loc_data["source_type"], int)

        # Text fields should be either str or None
        text_fields = ["source_name", "gen_desc", "ecology", "species", "notes", "refs"]
        for field in text_fields:
            assert isinstance(loc_data[field], (str, type(None)))

    # Test that all required fields are present
    required_fields = {
        "_id",
        "location_id",
        "source_type",
        "source_name",
        "gen_desc",
        "ecology",
        "species",
        "notes",
        "refs",
    }
    for loc_data in result.values():
        assert all(field in loc_data for field in required_fields)

    # Test that non-existent locations are not included
    assert 999 not in result

    # Test that all locations from input are processed
    assert len(result) == len(test_data)


def test_process_locations():
    # Sample test data based on locations.csv
    test_data = [
        {
            "id": "1",
            "name": "Albion, Mendocino Co., California, USA",
            "north": "39.2407989502",
            "south": "39.2153015137",
            "east": "-123.7379989624",
            "west": "-123.7779998779",
            "high": "100",
            "low": "0",
        },
        {
            "id": "2",
            "name": "Burbank, Los Angeles Co., California, USA",
            "north": "34.2216529846",
            "south": "34.1423683167",
            "east": "-118.2801055908",
            "west": "-118.3703155518",
            "high": "294",
            "low": "148",
        },
        {
            "id": "3",
            "name": "Mitrula Marsh, Tahoe National Forest, Sierra Co., California, USA",
            "north": "39.6272010803",
            "south": "39.6226005554",
            "east": "-120.6139984131",
            "west": "-120.6200027466",
            "high": "NULL",
            "low": "NULL",
        },
    ]

    result = process_locations(test_data)

    # Test basic structure
    assert isinstance(result, dict)

    # Test first location
    loc1 = result[1]
    assert loc1["_id"] == 1
    assert loc1["name"] == "Albion, Mendocino Co., California, USA"
    assert loc1["north"] == 39.2407989502
    assert loc1["south"] == 39.2153015137
    assert loc1["east"] == -123.7379989624
    assert loc1["west"] == -123.7779998779
    assert loc1["high"] == 100
    assert loc1["low"] == 0

    # Test location with NULL values
    loc3 = result[3]
    assert loc3["_id"] == 3
    assert (
        loc3["name"]
        == "Mitrula Marsh, Tahoe National Forest, Sierra Co., California, USA"
    )
    assert loc3["north"] == 39.6272010803
    assert loc3["south"] == 39.6226005554
    assert loc3["east"] == -120.6139984131
    assert loc3["west"] == -120.6200027466
    assert loc3["high"] is None
    assert loc3["low"] is None


def test_process_name_classifications():
    # Sample test data based on name_classifications.csv
    test_data = [
        {
            "name_id": "1",
            "domain": "Eukarya",
            "kingdom": "",
            "phylum": "",
            "class": "",
            "order": "",
            "family": "",
        },
        {
            "name_id": "2",
            "domain": "Eukarya",
            "kingdom": "Fungi",
            "phylum": "Ascomycota",
            "class": "Sordariomycetes",
            "order": "Xylariales",
            "family": "Xylariaceae",
        },
        {
            "name_id": "12",
            "domain": "",
            "kingdom": "Fungi",
            "phylum": "Ascomycota",
            "class": "Ascomycetes",
            "order": "Pezizales",
            "family": "Morchellaceae",
        },
        {
            "name_id": "13",
            "domain": "Eukarya",
            "kingdom": "Protozoa",
            "phylum": "",
            "class": "",
            "order": "",
            "family": "",
        },
        {
            "name_id": "14",
            "domain": "Eukarya",
            "kingdom": "Fungi",
            "phylum": "Basidiomycota",
            "class": "Agaricomycetes",
            "order": "",
            "family": "",
        },
    ]

    result = process_name_classifications(test_data)

    # Test basic structure
    assert isinstance(result, dict)

    # Test complete classification
    class2 = result[2]
    assert class2["_id"] == 2
    assert class2["domain"] == "Eukarya"
    assert class2["kingdom"] == "Fungi"
    assert class2["phylum"] == "Ascomycota"
    assert class2["class"] == "Sordariomycetes"
    assert class2["order"] == "Xylariales"
    assert class2["family"] == "Xylariaceae"

    # Test partial classification
    class1 = result[1]
    assert class1["_id"] == 1
    assert class1["domain"] == "Eukarya"
    assert class1["kingdom"] is None
    assert class1["phylum"] is None
    assert class1["class"] is None
    assert class1["order"] is None
    assert class1["family"] is None

    # Test missing domain
    class12 = result[12]
    assert class12["_id"] == 12
    assert class12["domain"] is None
    assert class12["kingdom"] == "Fungi"
    assert class12["phylum"] == "Ascomycota"

    # Test partial classification with some middle ranks
    class14 = result[14]
    assert class14["_id"] == 14
    assert class14["domain"] == "Eukarya"
    assert class14["kingdom"] == "Fungi"
    assert class14["phylum"] == "Basidiomycota"
    assert class14["class"] == "Agaricomycetes"
    assert class14["order"] is None
    assert class14["family"] is None

    # Test data type conversions
    for class_id, class_data in result.items():
        assert isinstance(class_id, int)
        assert isinstance(class_data["_id"], int)
        for field in ["domain", "kingdom", "phylum", "class", "order", "family"]:
            assert isinstance(class_data[field], (str, type(None)))

    # Test taxonomic hierarchy logic
    for class_data in result.values():
        # Test that if a rank is present, all higher ranks should be present
        if class_data["family"]:
            assert all(
                class_data[rank] for rank in ["order", "class", "phylum", "kingdom"]
            )
        if class_data["order"]:
            assert all(class_data[rank] for rank in ["class", "phylum", "kingdom"])
        if class_data["class"]:
            assert all(class_data[rank] for rank in ["phylum", "kingdom"])
        if class_data["phylum"]:
            assert class_data["kingdom"]

    # Test that all required fields are present
    required_fields = {"_id", "domain", "kingdom", "phylum", "class", "order", "family"}
    for class_data in result.values():
        assert all(field in class_data for field in required_fields)

    # Test that non-existent classifications are not included
    assert 999 not in result

    # Test that all classifications from input are processed
    assert len(result) == len(test_data)


def test_process_name_descriptions():
    # Sample test data based on name_descriptions.csv
    test_data = [
        {
            "id": "6",
            "name_id": "13",
            "source_type": "1",
            "source_name": "",
            "general_description": "",
            "diagnostic_description": "",
            "distribution": "",
            "habitat": "",
            "look_alikes": "",
            "uses": "",
            "notes": 'Images of Myxomycetes\n\n1. "http://naturalhistory.uga.edu/~GMNH/Mycoherb_Site/myxogal.htm"...',
            "refs": "",
        },
        {
            "id": "8",
            "name_id": "16",
            "source_type": "1",
            "source_name": "",
            "general_description": "http://en.wikipedia.org/wiki/Panellus_stipticus\n\nhttp://www.mushroomexpert.com/panellus_stipticus.html",
            "diagnostic_description": "",
            "distribution": "widely distributed",
            "habitat": "On the wood of broadleaf trees",
            "look_alikes": "",
            "uses": "",
            "notes": "Current Name:\nPanellus stipticus (Bull.) P. Karst....",
            "refs": "http://www.speciesfungorum.org/Names/SynSpecies.asp?RecordID=355858",
        },
        {
            "id": "11",
            "name_id": "23",
            "source_type": "1",
            "source_name": "",
            "general_description": "http://www.rogersmushrooms.com/gallery/DisplayBlock~bid~6894.asp",
            "diagnostic_description": "",
            "distribution": "Eastern North America",
            "habitat": "Under conifers and in mixed woods",
            "look_alikes": "",
            "uses": "Edible.",
            "notes": "Tylopilus chromapes (Frost) A.H. Sm. & Thiers...",
            "refs": "http://www.indexfungorum.org/names/NamesRecord.asp?RecordID=325151",
        },
    ]

    result = process_name_descriptions(test_data)

    # Test basic structure
    assert isinstance(result, dict)

    # Test description with minimal data
    desc6 = result[6]
    assert desc6["_id"] == 6
    assert desc6["name_id"] == 13
    assert desc6["source_type"] == 1
    assert desc6["source_name"] is None
    assert desc6["general_description"] is None
    assert desc6["notes"].startswith("Images of Myxomycetes")
    assert desc6["refs"] is None

    # Test description with more complete data
    desc8 = result[8]
    assert desc8["_id"] == 8
    assert desc8["name_id"] == 16
    assert desc8["distribution"] == "widely distributed"
    assert desc8["habitat"] == "On the wood of broadleaf trees"
    assert desc8["general_description"].startswith("http://")
    assert desc8["refs"].startswith("http://")

    # Test description with uses field
    desc11 = result[11]
    assert desc11["_id"] == 11
    assert desc11["name_id"] == 23
    assert desc11["distribution"] == "Eastern North America"
    assert desc11["habitat"] == "Under conifers and in mixed woods"
    assert desc11["uses"] == "Edible."

    # Test data type conversions
    for desc_id, desc_data in result.items():
        assert isinstance(desc_id, int)
        assert isinstance(desc_data["_id"], int)
        assert isinstance(desc_data["name_id"], int)
        assert isinstance(desc_data["source_type"], int)

        # Text fields should be either str or None
        text_fields = [
            "source_name",
            "general_description",
            "diagnostic_description",
            "distribution",
            "habitat",
            "look_alikes",
            "uses",
            "notes",
            "refs",
        ]
        for field in text_fields:
            assert isinstance(desc_data[field], (str, type(None)))

    # Test text field cleaning
    for desc_data in result.values():
        for field in ["notes", "general_description", "diagnostic_description"]:
            if desc_data[field]:
                # No trailing/leading whitespace
                assert desc_data[field].strip() == desc_data[field]
                # No empty lines at start/end
                assert not desc_data[field].startswith("\n")
                assert not desc_data[field].endswith("\n")

    # Test that all required fields are present
    required_fields = {
        "_id",
        "name_id",
        "source_type",
        "source_name",
        "general_description",
        "diagnostic_description",
        "distribution",
        "habitat",
        "look_alikes",
        "uses",
        "notes",
        "refs",
    }
    for desc_data in result.values():
        assert all(field in desc_data for field in required_fields)

    # Test that non-existent descriptions are not included
    assert 999 not in result

    # Test that all descriptions from input are processed
    assert len(result) == len(test_data)


def test_process_names():
    # Sample test data based on names.csv
    test_data = [
        {
            "id": "1",
            "text_name": "Fungi",
            "author": "Bartl.",
            "deprecated": "0",
            "correct_spelling_id": "NULL",
            "synonym_id": "9996",
            "rank": "14",
        },
        {
            "id": "2",
            "text_name": "Xylaria polymorpha group",
            "author": "J.D. Rogers",
            "deprecated": "0",
            "correct_spelling_id": "NULL",
            "synonym_id": "8975",
            "rank": "16",
        },
        {
            "id": "16",
            "text_name": "Panellus stipticus",
            "author": "(Bull.) P. Karst.",
            "deprecated": "0",
            "correct_spelling_id": "NULL",
            "synonym_id": "2663",
            "rank": "4",
        },
        {
            "id": "23",
            "text_name": "Tylopilus chromapes",
            "author": "(Frost) A.H. Sm. & Thiers",
            "deprecated": "1",
            "correct_spelling_id": "NULL",
            "synonym_id": "682",
            "rank": "4",
        },
    ]

    result = process_names(test_data)

    # Test basic structure
    assert isinstance(result, dict)

    # Test basic name
    name1 = result[1]
    assert name1["_id"] == 1
    assert name1["text_name"] == "Fungi"
    assert name1["author"] == "Bartl."
    assert name1["deprecated"] is False
    assert name1["correct_spelling_id"] is None
    assert name1["synonym_id"] == 9996
    assert name1["rank"] == 14

    # Test name with group designation
    name2 = result[2]
    assert name2["_id"] == 2
    assert name2["text_name"] == "Xylaria polymorpha group"
    assert name2["author"] == "J.D. Rogers"
    assert name2["rank"] == 16

    # Test species name
    name16 = result[16]
    assert name16["_id"] == 16
    assert name16["text_name"] == "Panellus stipticus"
    assert name16["author"] == "(Bull.) P. Karst."
    assert name16["deprecated"] is False
    assert name16["rank"] == 4

    # Test deprecated name
    name23 = result[23]
    assert name23["_id"] == 23
    assert name23["text_name"] == "Tylopilus chromapes"
    assert name23["deprecated"] is True
    assert name23["synonym_id"] == 682

    # Test data type conversions
    for name_id, name_data in result.items():
        assert isinstance(name_id, int)
        assert isinstance(name_data["_id"], int)
        assert isinstance(name_data["text_name"], str)
        assert isinstance(name_data["author"], str)
        assert isinstance(name_data["deprecated"], bool)
        assert isinstance(name_data["correct_spelling_id"], (int, type(None)))
        assert isinstance(name_data["synonym_id"], (int, type(None)))
        assert isinstance(name_data["rank"], int)

    # Test name format validation
    for name_data in result.values():
        # Text name should not have leading/trailing whitespace
        assert name_data["text_name"].strip() == name_data["text_name"]
        # Author should not have leading/trailing whitespace
        assert name_data["author"].strip() == name_data["author"]

    # Test that all required fields are present
    required_fields = {
        "_id",
        "text_name",
        "author",
        "deprecated",
        "correct_spelling_id",
        "synonym_id",
        "rank",
    }
    for name_data in result.values():
        assert all(field in name_data for field in required_fields)

    # Test that non-existent names are not included
    assert 999 not in result

    # Test that all names from input are processed
    assert len(result) == len(test_data)


def test_process_observations():
    # Sample test data based on observations.csv
    test_data = [
        {
            "id": "1",
            "name_id": "2",
            "when": "2004-07-13",
            "location_id": "214",
            "lat": "NULL",
            "lng": "NULL",
            "alt": "NULL",
            "vote_cache": "1.92335",
            "is_collection_location": "1",
            "thumb_image_id": "1",
        },
        {
            "id": "15",
            "name_id": "12",
            "when": "2005-02-05",
            "location_id": "69",
            "lat": "NULL",
            "lng": "NULL",
            "alt": "NULL",
            "vote_cache": "NULL",
            "is_collection_location": "1",
            "thumb_image_id": "18",
        },
        {
            "id": "35",
            "name_id": "28",
            "when": "2005-01-07",
            "location_id": "58",
            "lat": "NULL",
            "lng": "NULL",
            "alt": "NULL",
            "vote_cache": "NULL",
            "is_collection_location": "0",
            "thumb_image_id": "42",
        },
    ]

    result = process_observations(test_data)

    # Test basic structure
    assert isinstance(result, dict)

    # Test basic observation
    obs1 = result[1]
    assert obs1["_id"] == 1
    assert obs1["name_id"] == 2
    assert obs1["when"] == "2004-07-13"
    assert obs1["location_id"] == 214
    assert obs1["lat"] is None
    assert obs1["lng"] is None
    assert obs1["alt"] is None
    assert obs1["vote_cache"] == 1.92335
    assert obs1["is_collection_location"] is True
    assert obs1["thumb_image_id"] == 1

    # Test observation with NULL vote_cache
    obs15 = result[15]
    assert obs15["_id"] == 15
    assert obs15["vote_cache"] is None
    assert obs15["is_collection_location"] is True
    assert obs15["thumb_image_id"] == 18

    # Test observation with is_collection_location = 0
    obs35 = result[35]
    assert obs35["_id"] == 35
    assert obs35["is_collection_location"] is False
    assert obs35["vote_cache"] is None

    # Test data
