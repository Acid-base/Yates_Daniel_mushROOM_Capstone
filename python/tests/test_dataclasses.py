"""Tests for dataclasses used in the data pipeline."""

from datetime import datetime

# Import dataclasses from your data_csv.py (replace with your actual import)
from src.data_csv import BoundingBox, ImageMetadata, License


class TestDataclasses:
    def test_bounding_box(self):
        """Test the BoundingBox dataclass."""
        bbox = BoundingBox(
            north=45.0, south=44.0, east=-122.0, west=-123.0, high=1000.0, low=0.0
        )

        assert bbox.center == (44.5, -122.5)
        assert bbox.dimensions == (1.0, 1.0)
        assert bbox.elevation_range == (0.0, 1000.0)

    def test_image_metadata(self):
        """Test the ImageMetadata dataclass."""
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

        # Test that the object was created successfully (assertions from test_csv_data.py)
        assert metadata._id == 1
        assert metadata.url == "https://example.com/image.jpg"
        assert metadata.license == License.CC_BY
        assert metadata.copyright_holder == "Test User"
        assert metadata.date == datetime(2023, 1, 1)
        assert metadata.width == 800
        assert metadata.height == 600
        assert metadata.observation_id == 123

        # Test the crop bounding box (assertions from test_csv_data.py)
        assert metadata.crop.north == 45.0
        assert metadata.crop.south == 44.0
        assert metadata.crop.east == -122.0
        assert metadata.crop.west == -123.0


# --- Further improvements for test_dataclasses.py ---
# 1. If you add more dataclasses, create test classes and test functions for them in this file.
# 2. Expand test cases within each dataclass test to cover more initialization scenarios, property calculations, and method behaviors.
# 3. Consider adding tests for data validation within dataclasses if you implement any validation logic in them.
