import unittest
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd

from python.src.pipeline.pipeline import (
    CONFIG,
    calculate_data_quality_metrics,
    clean_dataframe,
    clean_location_descriptions,
    clean_locations,
    clean_name_descriptions,
    clean_names,
    clean_observations,
    clean_text,
    connect_to_mongodb,
    diff_dataframes,
    load_and_clean_csv,
    preprocess_all_csv_files,
    process_file,
    safe_float_convert,
    save_dataframe,
    transform_for_upsert,
    upsert_to_mongodb,
    validate_dataframe,
)


class TestPipeline(unittest.TestCase):
    """Tests for the data processing pipeline."""

    def setUp(self) -> None:
        """Sets up sample data for testing."""
        self.sample_df = pd.DataFrame(
            {
                "id": [1, 2, 3],
                "text_name": ["Name1", "Name2", "Name3"],
                "author": ["Author1", "Author2", "Author3"],
                "when": ["2021-01-01", "2021-02-01", None],
                "lat": ["12.34", "56.78", "invalid"],
                "lng": ["98.76", "invalid", "54.32"],
                "gen_desc": ["Description 1", "Description 2", "Description 3"],
                "ecology": ["Ecology 1", "Ecology 2", "Ecology 3"],
                "species": ["Species 1", "Species 2", "Species 3"],
                "notes": ["Notes 1", "Notes 2", "Notes 3"],
                "refs": ["Refs 1", "Refs 2", "Refs 3"],
                "name": ["Name 1", "Name 2", "Name 3"],
                "north": ["1.23", "4.56", "7.89"],
                "south": ["10.11", "12.13", "14.15"],
                "east": ["16.17", "18.19", "20.21"],
                "west": ["22.23", "24.25", "26.27"],
                "high": ["28.29", "30.31", "32.33"],
                "low": ["34.35", "36.37", "38.39"],
                "content_type": ["image/jpeg", "image/png", "image/gif"],
                "copyright_holder": [
                    "Copyright Holder 1",
                    "Copyright Holder 2",
                    "Copyright Holder 3",
                ],
                "license": ["License 1", "License 2", "License 3"],
                "ok_for_export": [True, False, True],
                "diagnostic": [True, False, True],
                "source_type": ["Source Type 1", "Source Type 2", "Source Type 3"],
                "source_name": ["Source Name 1", "Source Name 2", "Source Name 3"],
                "general_description": [
                    "General Description 1",
                    "General Description 2",
                    "General Description 3",
                ],
                "diagnostic_description": [
                    "Diagnostic Description 1",
                    "Diagnostic Description 2",
                    "Diagnostic Description 3",
                ],
                "distribution": ["Distribution 1", "Distribution 2", "Distribution 3"],
                "habitat": ["Habitat 1", "Habitat 2", "Habitat 3"],
                "look_alikes": ["Look Alikes 1", "Look Alikes 2", "Look Alikes 3"],
                "uses": ["Uses 1", "Uses 2", "Uses 3"],
                "domain": ["Domain 1", "Domain 2", "Domain 3"],
                "kingdom": ["Kingdom 1", "Kingdom 2", "Kingdom 3"],
                "phylum": ["Phylum 1", "Phylum 2", "Phylum 3"],
                "class": ["Class 1", "Class 2", "Class 3"],
                "order": ["Order 1", "Order 2", "Order 3"],
                "family": ["Family 1", "Family 2", "Family 3"],
                "image_id": [4, 5, 6],
                "observation_id": [7, 8, 9],
            },
        )

    def test_safe_float_convert(self) -> None:
        """Tests the safe_float_convert function."""
        assert safe_float_convert("12.34") == 12.34
        assert pd.isna(safe_float_convert("invalid"))

    def test_clean_text(self) -> None:
        """Tests the clean_text function."""
        series = pd.Series(["<b>Hello</b> World", "   Trimmed text   "])
        cleaned = clean_text(series)
        assert cleaned[0] == "Hello World"
        assert cleaned[1] == "Trimmed text"

    def test_clean_dataframe(self) -> None:
        """Tests the clean_dataframe function."""
        cleaned_df = clean_dataframe(
            self.sample_df,
            {"text_name": clean_text, "author": lambda x: x.str.strip()},
        )
        assert cleaned_df["author"][0] == "Author1"

    def test_clean_location_descriptions(self) -> None:
        """Tests the clean_location_descriptions function."""
        location_descriptions_df = clean_location_descriptions(self.sample_df)
        assert pd.api.types.is_integer_dtype(location_descriptions_df["id"])
        assert all(
            location_descriptions_df["gen_desc"].apply(lambda x: isinstance(x, str))
        )
        assert all(
            location_descriptions_df["ecology"].apply(lambda x: isinstance(x, str))
        )
        assert all(
            location_descriptions_df["species"].apply(lambda x: isinstance(x, str))
        )
        assert all(
            location_descriptions_df["notes"].apply(lambda x: isinstance(x, str))
        )
        assert all(location_descriptions_df["refs"].apply(lambda x: isinstance(x, str)))

    def test_clean_locations(self) -> None:
        """Tests the clean_locations function."""
        locations_df = clean_locations(self.sample_df)
        assert pd.api.types.is_integer_dtype(locations_df["id"])
        assert all(
            locations_df["name"].apply(lambda x: isinstance(x, (float, int, pd.NA)))
        )
        assert all(
            locations_df["north"].apply(lambda x: isinstance(x, (float, int, pd.NA)))
        )
        assert all(
            locations_df["south"].apply(lambda x: isinstance(x, (float, int, pd.NA)))
        )
        assert all(
            locations_df["east"].apply(lambda x: isinstance(x, (float, int, pd.NA)))
        )
        assert all(
            locations_df["west"].apply(lambda x: isinstance(x, (float, int, pd.NA)))
        )
        assert all(
            locations_df["high"].apply(lambda x: isinstance(x, (float, int, pd.NA)))
        )
        assert all(
            locations_df["low"].apply(lambda x: isinstance(x, (float, int, pd.NA)))
        )

    @patch("pipeline.pd.read_csv")
    def test_load_and_clean_csv(self, mock_read_csv: MagicMock) -> None:
        """Tests the load_and_clean_csv function."""
        # Load real CSV data
        real_df = pd.read_csv(
            "tests/data/your_csv_file.csv",
            sep="\t",
            header=0,
            low_memory=False,
            converters={},
            na_values=["NULL"],
        )
        mock_read_csv.return_value = real_df
        cleaned_df = load_and_clean_csv(
            "tests/data/your_csv_file.csv",
            clean_names,
            {},
        )
        assert not cleaned_df.empty
        # Add more assertions to check the cleaned data
        assert pd.api.types.is_integer_dtype(cleaned_df["id"])
        assert all(cleaned_df["text_name"].apply(lambda x: isinstance(x, str)))
        # ... other assertions ...

    @patch("pipeline.os.makedirs")
    @patch("pipeline.pd.DataFrame.to_csv")
    def test_save_dataframe(
        self,
        mock_to_csv: MagicMock,
        mock_makedirs: MagicMock,
    ) -> None:
        """Tests the save_dataframe function."""
        save_dataframe(self.sample_df, "dummy.csv", format="csv")
        mock_makedirs.assert_called_once()
        mock_to_csv.assert_called_once()

    def test_validate_dataframe(self) -> None:
        """Tests the validate_dataframe function."""
        assert validate_dataframe(self.sample_df, ["id", "text_name", "author"])
        assert not validate_dataframe(self.sample_df, ["non_existing_column"])

    @patch("pipeline.logger")
    def test_diff_dataframes(self, mock_logger: MagicMock) -> None:
        """Tests the diff_dataframes function."""
        df1 = self.sample_df
        df2 = self.sample_df.copy()  # Create a copy of the DataFrame
        df2["text_name"][0] = "Changed Name"
        diff_dataframes(df1, df2, "dummy.csv")
        mock_logger.info.assert_called()

    def test_transform_for_upsert(self) -> None:
        """Tests the transform_for_upsert function."""
        transform_for_upsert(self.sample_df)  # Just call the function

    def test_clean_names(self) -> None:
        """Tests the clean_names function."""
        names_df = clean_names(self.sample_df)
        assert pd.api.types.is_integer_dtype(names_df["id"])
        assert all(names_df["text_name"].apply(lambda x: isinstance(x, str)))
        assert all(names_df["author"].apply(lambda x: isinstance(x, str)))
        assert all(names_df["deprecated"].apply(lambda x: isinstance(x, bool)))

    def test_clean_observations(self) -> None:
        """Tests the clean_observations function."""
        observations_df = clean_observations(self.sample_df)
        assert all(
            observations_df["when"].apply(
                lambda x: isinstance(x, pd.Timestamp) or pd.isna(x)
            )
        )
        assert all(observations_df["notes"].apply(lambda x: isinstance(x, str)))
        assert all(
            observations_df["lat"].apply(lambda x: isinstance(x, (float, int, pd.NA)))
        )
        assert all(
            observations_df["lng"].apply(lambda x: isinstance(x, (float, int, pd.NA)))
        )
        assert all(
            observations_df["alt"].apply(lambda x: isinstance(x, (float, int, pd.NA)))
        )

    def test_clean_name_descriptions(self) -> None:
        """Tests the clean_name_descriptions function."""
        name_descriptions_df = clean_name_descriptions(self.sample_df)
        assert pd.api.types.is_integer_dtype(name_descriptions_df["id"])
        assert all(
            name_descriptions_df["general_description"].apply(
                lambda x: isinstance(x, str)
            )
        )
        assert all(
            name_descriptions_df["diagnostic_description"].apply(
                lambda x: isinstance(x, str)
            )
        )
        assert all(
            name_descriptions_df["distribution"].apply(lambda x: isinstance(x, str))
        )
        assert all(name_descriptions_df["habitat"].apply(lambda x: isinstance(x, str)))
        assert all(
            name_descriptions_df["look_alikes"].apply(lambda x: isinstance(x, str))
        )
        assert all(name_descriptions_df["uses"].apply(lambda x: isinstance(x, str)))
        assert all(name_descriptions_df["notes"].apply(lambda x: isinstance(x, str)))
        assert all(name_descriptions_df["refs"].apply(lambda x: isinstance(x, str)))

    @patch("pipeline.load_and_clean_csv")
    @patch("pipeline.validate_dataframe")
    @patch("pipeline.transform_for_upsert")
    @patch("pipeline.save_dataframe")
    @patch("pipeline.diff_dataframes")
    @patch("pipeline.connect_to_mongodb")
    @patch("pipeline.upsert_to_mongodb")
    def test_process_file(
        self,
        mock_upsert_to_mongodb: MagicMock,
        mock_connect_to_mongodb: MagicMock,
        mock_diff_dataframes: MagicMock,
        mock_save_dataframe: MagicMock,
        mock_transform_for_upsert: MagicMock,
        mock_validate_dataframe: MagicMock,
        mock_load_and_clean_csv: MagicMock,
    ) -> None:
        """Tests the process_file function."""
        mock_load_and_clean_csv.return_value = self.sample_df
        mock_validate_dataframe.return_value = True
        mock_transform_for_upsert.return_value = self.sample_df
        process_file("dummy.csv", clean_names, {}, ["id", "text_name", "author"])
        mock_load_and_clean_csv.assert_called_once_with(
            "dummy.csv",
            clean_names,
            {},
        )
        mock_validate_dataframe.assert_called_once_with(
            self.sample_df,
            ["id", "text_name", "author"],
        )
        mock_transform_for_upsert.assert_called_once_with(self.sample_df)
        mock_connect_to_mongodb.assert_called_once_with(CONFIG["database"])
        mock_upsert_to_mongodb.assert_called_once()
        mock_diff_dataframes.assert_called_once_with(
            self.sample_df,
            self.sample_df,
            "dummy.csv",
        )
        mock_save_dataframe.assert_called()

    @patch("pipeline.MongoClient")
    def test_connect_to_mongodb(self, mock_mongo_client: MagicMock) -> None:
        """Tests the connect_to_mongodb function."""
        connect_to_mongodb(CONFIG["database"])
        mock_mongo_client.assert_called_once_with(
            CONFIG["database"]["host"],
            CONFIG["database"]["port"],
        )

    @patch("pipeline.MongoClient")
    def test_upsert_to_mongodb(self, mock_mongo_client: MagicMock) -> None:
        """Tests the upsert_to_mongodb function."""
        mock_collection = MagicMock()
        mock_mongo_client.return_value.__getitem__.return_value = mock_collection
        upsert_to_mongodb(mock_collection, [{"id": 1}], "id")
        mock_collection.bulk_write.assert_called_once()

    @patch("pipeline.process_file")
    @patch("pipeline.ThreadPoolExecutor")
    def test_preprocess_all_csv_files(
        self,
        mock_executor: MagicMock,
        mock_process_file: MagicMock,
    ) -> None:
        """Tests the preprocess_all_csv_files function."""
        mock_executor.return_value.__enter__.return_value = MagicMock()
        preprocess_all_csv_files()
        mock_process_file.assert_called()

    @patch("pipeline.logger")
    def test_calculate_data_quality_metrics(self, mock_logger: MagicMock) -> None:
        """Tests the calculate_data_quality_metrics function."""
        calculate_data_quality_metrics(self.sample_df, "dummy.csv")
        mock_logger.info.assert_called()


class TestDataProcessing(unittest.TestCase):
    """Tests for data cleaning functions."""

    def test_safe_float_convert(self) -> None:
        """Tests the safe_float_convert function."""
        assert safe_float_convert("1.23") == 1.23
        assert safe_float_convert(1) == 1.0
        assert np.isnan(safe_float_convert("abc"))

    def test_clean_text(self) -> None:
        """Tests the clean_text function."""
        assert clean_text("<b>Hello</b> <i>world</i>!", 5) == "Hello"
        assert clean_text("  This is a test.  ") == "This is a test."

    def test_clean_names(self) -> None:
        """Tests the clean_names function."""
        data = pd.DataFrame(
            {
                "id": ["1", "2"],
                "text_name": ["<b>Name 1</b>", "Name 2"],
                "author": [" Author ", None],
            },
        )
        expected = pd.DataFrame(
            {
                "id": [1, 2],
                "text_name": ["Name 1", "Name 2"],
                "author": ["Author", None],
            },
        )
        pd.testing.assert_frame_equal(clean_names(data), expected)

    def test_clean_observations(self) -> None:
        """Tests the clean_observations function."""
        data = pd.DataFrame(
            {
                "id": ["1", "2"],
                "name_id": ["1", "2"],
                "when": ["2023-01-01", "2023-02-02"],
                "location_id": ["3", "4"],
                "notes": ["  Notes 1  ", "Notes 2"],
                "lat": ["12.34", "invalid"],
                "lng": ["98.76", "54.32"],
                "alt": ["100", "abc"],
            },
        )
        expected = pd.DataFrame(
            {
                "id": [1, 2],
                "name_id": [1, 2],
                "when": pd.to_datetime(["2023-01-01", "2023-02-02"]),
                "location_id": [3, 4],
                "notes": ["Notes 1", "Notes 2"],
                "lat": [12.34, np.nan],
                "lng": [98.76, 54.32],
                "alt": [100.0, np.nan],
            },
        )
        pd.testing.assert_frame_equal(clean_observations(data), expected)

    def test_clean_location_descriptions(self) -> None:
        """Tests the clean_location_descriptions function."""
        data = pd.DataFrame(
            {
                "id": ["1", "2"],
                "location_id": ["3", "4"],
                "gen_desc": ["<b>Description 1</b>", "Description 2"],
                "ecology": ["  Ecology 1  ", "Ecology 2"],
                "species": ["Species 1", "Species 2"],
                "notes": ["Notes 1", "Notes 2"],
                "refs": ["Refs 1", "Refs 2"],
            },
        )
        expected = pd.DataFrame(
            {
                "id": [1, 2],
                "location_id": [3, 4],
                "gen_desc": ["Description 1", "Description 2"],
                "ecology": ["Ecology 1", "Ecology 2"],
                "species": ["Species 1", "Species 2"],
                "notes": ["Notes 1", "Notes 2"],
                "refs": ["Refs 1", "Refs 2"],
            },
        )
        pd.testing.assert_frame_equal(
            clean_location_descriptions(data),
            expected,
        )

    def test_clean_locations(self) -> None:
        """Tests the clean_locations function."""
        data = pd.DataFrame(
            {
                "id": ["1", "2"],
                "name": ["Name 1", "Name 2"],
                "north": ["1.23", "invalid"],
                "south": ["10.11", "12.13"],
                "east": ["16.17", "18.19"],
                "west": ["22.23", "24.25"],
                "high": ["28.29", "abc"],
                "low": ["34.35", "36.37"],
            },
        )
        expected = pd.DataFrame(
            {
                "id": [1, 2],
                "name": ["Name 1", "Name 2"],
                "north": [1.23, np.nan],
                "south": [10.11, 12.13],
                "east": [16.17, 18.19],
                "west": [22.23, 24.25],
                "high": [28.29, np.nan],
                "low": [34.35, 36.37],
            },
        )
        pd.testing.assert_frame_equal(clean_locations(data), expected)

    def test_clean_name_descriptions(self) -> None:
        """Tests the clean_name_descriptions function."""
        data = pd.DataFrame(
            {
                "id": ["1", "2"],
                "name_id": ["3", "4"],
                "general_description": ["<b>Description 1</b>", "Description 2"],
                "diagnostic_description": ["  Description 1  ", "Description 2"],
                "distribution": ["Distribution 1", "Distribution 2"],
                "habitat": ["Habitat 1", "Habitat 2"],
                "look_alikes": ["Look Alikes 1", "Look Alikes 2"],
                "uses": ["Uses 1", "Uses 2"],
                "notes": ["Notes 1", "Notes 2"],
                "refs": ["Refs 1", "Refs 2"],
            },
        )
        expected = pd.DataFrame(
            {
                "id": [1, 2],
                "name_id": [3, 4],
                "general_description": ["Description 1", "Description 2"],
                "diagnostic_description": ["Description 1", "Description 2"],
                "distribution": ["Distribution 1", "Distribution 2"],
                "habitat": ["Habitat 1", "Habitat 2"],
                "look_alikes": ["Look Alikes 1", "Look Alikes 2"],
                "uses": ["Uses 1", "Uses 2"],
                "notes": ["Notes 1", "Notes 2"],
                "refs": ["Refs 1", "Refs 2"],
            },
        )
        pd.testing.assert_frame_equal(
            clean_name_descriptions(data),
            expected,
        )


if __name__ == "__main__":
    unittest.main()
