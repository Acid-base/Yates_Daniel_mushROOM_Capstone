"""Tests for CSV data processing."""

import pytest
import pandas as pd
from pathlib import Path
from data_csv import CSVProcessor
from config import DataConfig


@pytest.fixture
def csv_config(test_data_dir):
    """Create test configuration."""
    return DataConfig(
        MONGODB_URI="mongodb://test:27017",
        DATABASE_NAME="test_db",
        DATA_DIR=test_data_dir,
        CHUNK_SIZE=1024,
    )


@pytest.fixture
def processor(csv_config):
    """Create CSV processor instance."""
    return CSVProcessor(csv_config)


@pytest.fixture
def test_csv_file(test_data_dir):
    """Create a test CSV file."""
    csv_path = test_data_dir / "test.csv"
    data = pd.DataFrame(
        {
            "id": range(1, 11),
            "name": [f"Name {i}" for i in range(1, 11)],
            "value": [i * 1.5 for i in range(1, 11)],
        }
    )
    data.to_csv(csv_path, index=False)
    return csv_path


def test_processor_initialization(processor):
    """Test CSVProcessor initialization."""
    assert processor.chunk_size == 1024
    assert processor.config is not None


def test_read_csv_file(processor, test_csv_file):
    """Test reading a CSV file."""
    df = processor.read_file(test_csv_file)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 10
    assert all(col in df.columns for col in ["id", "name", "value"])


def test_read_csv_in_chunks(processor, test_csv_file):
    """Test reading CSV file in chunks."""
    processor.chunk_size = 3  # Small chunk size for testing
    chunks = list(processor.read_chunks(test_csv_file))

    assert len(chunks) == 4  # 10 rows with chunk_size=3 should yield 4 chunks
    assert sum(len(chunk) for chunk in chunks) == 10  # Total rows should match
    assert all(isinstance(chunk, pd.DataFrame) for chunk in chunks)


def test_read_nonexistent_file(processor):
    """Test reading a non-existent file."""
    with pytest.raises(FileNotFoundError):
        processor.read_file(Path("nonexistent.csv"))


def test_process_empty_file(processor, test_data_dir):
    """Test processing an empty CSV file."""
    empty_file = test_data_dir / "empty.csv"
    empty_file.write_text("id,name,value\n")

    df = processor.read_file(empty_file)
    assert len(df) == 0
    assert list(df.columns) == ["id", "name", "value"]


def test_handle_missing_values(processor, test_data_dir):
    """Test handling missing values in CSV."""
    csv_path = test_data_dir / "missing.csv"
    data = "id,name,value\n1,Name 1,1.5\n2,,\n3,Name 3,3.5\n"
    csv_path.write_text(data)

    df = processor.read_file(csv_path)
    assert len(df) == 3
    assert pd.isna(df.loc[1, "name"])
    assert pd.isna(df.loc[1, "value"])


def test_custom_chunk_processing(processor, test_csv_file):
    """Test processing with custom chunk size."""

    def process_chunk(chunk):
        chunk["value"] = chunk["value"] * 2
        return chunk

    processor.chunk_size = 2
    processed_chunks = []
    for chunk in processor.read_chunks(test_csv_file):
        processed_chunks.append(process_chunk(chunk))

    result = pd.concat(processed_chunks)
    assert len(result) == 10
    assert all(result["value"] == pd.Series(range(1, 11)) * 3.0)


def test_handle_malformed_csv(processor, test_data_dir):
    """Test handling malformed CSV data."""
    csv_path = test_data_dir / "malformed.csv"
    data = "id,name,value\n1,Name 1,1.5\nmalformed_row\n3,Name 3,3.5\n"
    csv_path.write_text(data)

    with pytest.raises(pd.errors.ParserError):
        processor.read_file(csv_path)


def test_large_file_processing(processor, test_data_dir):
    """Test processing a larger CSV file."""
    csv_path = test_data_dir / "large.csv"

    # Create a larger dataset
    data = pd.DataFrame(
        {
            "id": range(1000),
            "name": [f"Name {i}" for i in range(1000)],
            "value": [i * 1.5 for i in range(1000)],
        }
    )
    data.to_csv(csv_path, index=False)

    # Process in chunks
    processor.chunk_size = 100
    chunks = list(processor.read_chunks(csv_path))

    assert len(chunks) == 10  # 1000 rows / 100 chunk_size
    assert all(len(chunk) == 100 for chunk in chunks[:-1])  # All but last chunk
    assert sum(len(chunk) for chunk in chunks) == 1000


def test_data_type_inference(processor, test_data_dir):
    """Test CSV data type inference."""
    csv_path = test_data_dir / "types.csv"
    data = "id,name,value,date\n1,Name 1,1.5,2023-01-01\n2,Name 2,2.5,2023-01-02\n"
    csv_path.write_text(data)

    df = processor.read_file(csv_path)

    assert df["id"].dtype == "int64"
    assert df["name"].dtype == "object"
    assert df["value"].dtype == "float64"
    assert df["date"].dtype == "object"  # or datetime64 if parse_dates is used


def test_file_encoding_handling(processor, test_data_dir):
    """Test handling different file encodings."""
    csv_path = test_data_dir / "encoded.csv"
    data = "id,name,value\n1,Name €,1.5\n2,Name £,2.5\n"

    # Write with specific encoding
    csv_path.write_text(data, encoding="utf-8")
    df = processor.read_file(csv_path)
    assert "€" in df["name"].values
    assert "£" in df["name"].values


def test_processor_memory_usage(processor, test_data_dir):
    """Test memory efficient processing of CSV files."""
    csv_path = test_data_dir / "memory.csv"

    # Create a moderate-sized dataset
    data = pd.DataFrame(
        {
            "id": range(10000),
            "name": [f"Name {i}" for i in range(10000)],
            "value": [i * 1.5 for i in range(10000)],
        }
    )
    data.to_csv(csv_path, index=False)

    # Process with small chunks to test memory efficiency
    processor.chunk_size = 100
    chunk_count = 0
    max_memory = 0

    for chunk in processor.read_chunks(csv_path):
        chunk_count += 1
        # Check memory usage of each chunk
        memory_usage = chunk.memory_usage(deep=True).sum()
        max_memory = max(max_memory, memory_usage)

        # Each chunk should be approximately the same size
        assert len(chunk) <= processor.chunk_size

    assert chunk_count == 100  # 10000 rows / 100 chunk_size
    # Memory usage should be bounded
    assert max_memory < 1e6  # Less than 1MB per chunk
