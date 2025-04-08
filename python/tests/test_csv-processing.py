"""Tests for CSV processing functions and CSVProcessor class."""

import pytest
import pandas as pd
from io import StringIO

# Import CSV processing functions and CSVProcessor from your data_csv.py (replace with your actual import)
from src.data_csv import (
    CSVProcessor,
    clean_names_csv,
    clean_name_descriptions_csv,
    clean_name_classifications_csv,
)

# --- Test Data (Simulated CSV Content as Strings) - Reusing from previous tests ---
NAMES_CSV_TEST_DATA = """id\ttext_name\tauthor\tdeprecated\tcorrect_spelling_id\tsynonym_id\trank
1\tFungi\t\t0\t\t\t1
2\tAgaricus bisporus\t(J.E. Lange) Imbach\t0\t\t\t20
3\tAgaricus campestris group\t\t0\t\t\t15
4\tAgaricus silvaticus\tSchaeff.\t0\t\t\t20
5\tAgaricus sylvaticus\tHuds.\t1\t4\t\t20
6\tBoletus edulis\tBull.\t0\t\t\t20
7\tBoletus edulis group\t\t0\t\t\t15
8\tCantharellus cibarius\tFr.\t0\t\t\t20
9\tAmanita muscaria\t(L.) Lam.\t0\t\t\t20
10\tAmanita muscaria var. alba\t(Pers.) E.-J. Gilbert\t0\t9\t\t25
11\tClavaria zollingeri\tLév.\t0\t\t\t20
12\tClavariadelphus truncatus\t(Quél.) Donk\t0\t\t\t20
"""

NAME_DESCRIPTIONS_CSV_TEST_DATA = """id
1
name_id
1
source_type
1
source_name
System Import
gen_desc
General description for Fungi Kingdom.
diag_desc

habitat

look_alikes

uses

notes

refs

---
id
2
name_id
2
source_type
2
source_name
User: MycoEnthusiast
gen_desc
Detailed general description for Agaricus bisporus. Includes HTML <p>paragraph</p> tags.
diag_desc
Diagnostic features of Agaricus bisporus: brown cap, pink gills.
habitat
Cultivated, grassy areas.
look_alikes
Agaricus campestris, Agaricus bitorquis.
uses
Edible and widely cultivated.
notes
Some interesting notes about Agaricus bisporus.
refs
http://mushroomexpert.com/agaricus_bisporus.html

---
id
3
name_id
3
source_type
1
source_name
System Aggregate
gen_desc
General description for Agaricus campestris group.
diag_desc
Group diagnostic description.
habitat
Meadows, fields.
look_alikes
Multiple Agaricus species.
uses
Edible, some caution advised.
notes
Notes for the Agaricus campestris group.
refs
Reference for Agaricus campestris group.
"""

NAME_CLASSIFICATIONS_CSV_TEST_DATA = """id\tname_id\tdomain\tkingdom\tphylum\tclass\torder\tfamily
1\t1\tEukaryota\tFungi\t\t\t\t
2\t2\tEukaryota\tFungi\tBasidiomycota\tAgaricomycetes\tAgaricales\tAgaricaceae
3\t3\tEukaryota\tFungi\tBasidiomycota\tAgaricomycetes\tAgaricales\tAgaricaceae
4\t4\tEukaryota\tFungi\tBasidiomycota\tAgaricomycetes\tAgaricales\tAgaricaceae
5\t5\tEukaryota\tFungi\tBasidiomycota\tAgaricomycetes\tAgaricales\tAgaricaceae
6\t6\tEukaryota\tFungi\tBasidiomycota\tAgaricomycetes\tAgaricales\tBoletaceae
7\t7\tEukaryota\tFungi\tBasidiomycota\tAgaricomycetes\tBoletales\tBoletaceae
8\t8\tEukaryota\tFungi\tBasidiomycota\tAgaricomycetes\tAgaricales\tCantharellaceae
9\t9\tEukaryota\tFungi\tBasidiomycota\tAgaricomycetes\tAgaricales\tAmanitaceae
10\t10\tEukaryota\tFungi\tBasidiomycota\tAgaricomycetes\tAgaricales\tAmanitaceae
11\t11\tEukaryota\tFungi\tAscomycota\tSordariomycetes\tXylariales\tClavariaceae
12\t12\tEukaryota\tFungi\tBasidiomycota\tAgaricomycetes\tGomphales\tClavariadelphaceae
13\t13\tEukaryota\tPlantae\tTracheophyta\tMagnoliopsida\tRosales\tRosaceae
"""


class TestCSVProcessing:
    # --- CSVProcessor Tests ---
    def test_csv_processor_init(self, csv_config):
        """Test CSVProcessor initialization."""
        processor = CSVProcessor(csv_config)
        assert processor.config == csv_config
        assert processor.chunk_size == csv_config.CHUNK_SIZE

    def test_csv_processor_read_chunks(
        self, csv_config, sample_observations_df, tmp_path
    ):
        """Test reading CSV in chunks."""
        csv_path = tmp_path / "large.csv"
        # Create a larger dataset by repeating the sample
        large_df = pd.concat([sample_observations_df] * 10, ignore_index=True)
        large_df.to_csv(csv_path, index=False)

        processor = CSVProcessor(csv_config)
        chunks = list(processor.read_chunks(csv_path))

        assert len(chunks) > 1  # Should be split into multiple chunks
        total_rows = sum(len(chunk) for chunk in chunks)
        assert total_rows == len(large_df)

    def test_csv_processor_invalid_file(self, csv_config):
        """Test handling invalid CSV file."""
        processor = CSVProcessor(csv_config)
        with pytest.raises(FileNotFoundError):
            list(processor.read_chunks(Path("nonexistent.csv")))

    def test_csv_processor_custom_chunk_size(
        self, csv_config, sample_observations_df, tmp_path
    ):
        """Test CSV processing with custom chunk size."""
        csv_path = tmp_path / "test.csv"
        large_df = pd.concat([sample_observations_df] * 5, ignore_index=True)
        large_df.to_csv(csv_path, index=False)

        processor = CSVProcessor(csv_config, chunk_size=len(sample_observations_df))
        chunks = list(processor.read_chunks(csv_path))

        assert len(chunks) == 5  # Should be split into 5 chunks
        assert all(len(chunk) == len(sample_observations_df) for chunk in chunks[:-1])

    def test_csv_processor_data_validation(self, csv_config, tmp_path):
        """Test data validation in CSV processing."""
        invalid_df = pd.DataFrame(
            {
                "id": [1, 2, "invalid"],  # Mixed types
                "name": ["Test", None, "Test"],  # Contains null
            }
        )

        csv_path = tmp_path / "invalid.csv"
        invalid_df.to_csv(csv_path, index=False)

        processor = CSVProcessor(csv_config)
        chunks = list(processor.read_chunks(csv_path))

        # Should handle mixed types and null values
        assert all(chunk["id"].dtype == "object" for chunk in chunks)
        assert any(chunk["name"].isna().any() for chunk in chunks)

    # --- CSV Cleaning Function Tests ---
    def test_clean_names_csv(self):
        """Test cleaning function for names.csv."""
        names_df = pd.read_csv(StringIO(NAMES_CSV_TEST_DATA), sep="\t")
        cleaned_names_df = clean_names_csv(names_df.copy())

        # Assertions (same as in test_data_csv.py)
        assert "Agaricus campestris group" not in cleaned_names_df["text_name"].values
        assert (
            "Agaricus sylvaticus"
            not in cleaned_names_df[cleaned_names_df["id"] == 5]["text_name"].values
        )
        assert len(cleaned_names_df) == 10

    def test_clean_name_descriptions_csv(self):
        """Test cleaning function for name_descriptions.csv."""
        name_descriptions_df = pd.read_csv(
            StringIO(NAME_DESCRIPTIONS_CSV_TEST_DATA), sep="\n", header=None
        )
        data_list = []
        current_record = {}
        for _, row in name_descriptions_df.iterrows():
            line = row[0]
            if line == "---":
                if current_record:
                    data_list.append(current_record)
                current_record = {}
            elif line:
                key, value = line.split("\n", 1)
                current_record[key.strip()] = value.strip()

        name_descriptions_df_parsed = pd.DataFrame(data_list)
        cleaned_descriptions_df = clean_name_descriptions_csv(
            name_descriptions_df_parsed.copy()
        )

        # Assertions (same as in test_data_csv.py)
        assert cleaned_descriptions_df.shape[0] == 3
        agaricus_desc = cleaned_descriptions_df[cleaned_descriptions_df["name_id"] == 2]
        assert not agaricus_desc["gen_desc"].iloc[0].startswith("---")
        assert "<p>" not in agaricus_desc["gen_desc"].iloc[0]
        assert (
            "http://mushroomexpert.com/agaricus_bisporus.html"
            in cleaned_descriptions_df["refs"].iloc[1]
        )

    def test_clean_name_classifications_csv(self):
        """Test cleaning function for name_classifications.csv."""
        name_classifications_df = pd.read_csv(
            StringIO(NAME_CLASSIFICATIONS_CSV_TEST_DATA), sep="\t"
        )
        cleaned_classifications_df = clean_name_classifications_csv(
            name_classifications_df.copy()
        )

        # Assertions (same as in test_data_csv.py)
        assert "Plantae" not in cleaned_classifications_df["kingdom"].values
        assert cleaned_classifications_df["class_name"].dtype.name == "object"
        fungi_kingdom_row = cleaned_classifications_df[
            cleaned_classifications_df["name_id"] == 1
        ]
        assert fungi_kingdom_row["phylum"].iloc[0] is None
        assert cleaned_classifications_df.shape[0] == 12


# --- Further improvements for test_csv_processing.py ---
# 1. Add tests for cleaning functions of ALL CSV files (locations, location_descriptions, images, images_observations, observations).
# 2. Expand test cases within each cleaning function test to cover more data variations, edge cases, and invalid data scenarios.
# 3. Consider testing specific data transformations and aggregations in more detail within the cleaning function tests.
# 4. If you add more complex CSV loading logic or error handling in CSVProcessor or cleaning functions, add dedicated tests for those aspects.
