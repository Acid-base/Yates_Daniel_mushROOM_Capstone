"""API endpoint mapper for Mushroom Observer."""

import asyncio
import aiohttp
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import time

from config import DataConfig
from exceptions import DataProcessingError

logger = logging.getLogger(__name__)


class MOApiMapper:
    """Maps and tests Mushroom Observer API endpoints."""

    BASE_URL = "https://mushroomobserver.org/api2"
    REQUEST_DELAY = 20  # seconds between requests

    def __init__(self, config: DataConfig, output_dir: Path):
        self.config = config
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session: Optional[aiohttp.ClientSession] = None
        self.last_request_time = 0

        # Store discovered IDs
        self.example_ids = {
            "names": [],
            "observations": [],
            "images": [],
            "locations": [],
            "sequences": [],
            "external_links": [],
        }

    async def __aenter__(self):
        """Set up async context."""
        self.session = aiohttp.ClientSession(headers={"Accept": "application/json"})
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up async context."""
        if self.session:
            await self.session.close()

    async def _make_request(
        self, endpoint: str, params: Dict[str, str]
    ) -> Dict[str, Any]:
        """Make API request with rate limiting."""
        if not self.session:
            raise DataProcessingError("No active session")

        # Enforce rate limiting
        now = time.time()
        time_since_last = now - self.last_request_time
        if time_since_last < self.REQUEST_DELAY:
            await asyncio.sleep(self.REQUEST_DELAY - time_since_last)

        # Always request JSON format
        params["format"] = "json"

        url = f"{self.BASE_URL}/{endpoint}"
        try:
            async with self.session.get(url, params=params) as response:
                self.last_request_time = time.time()

                if response.status != 200:
                    raise DataProcessingError(
                        f"API request failed: {response.status} - {await response.text()}"
                    )

                return await response.json()

        except Exception as e:
            raise DataProcessingError(f"API request failed: {str(e)}")

    async def test_endpoint(
        self, endpoint: str, params: Dict[str, str], save_as: str
    ) -> Dict[str, Any]:
        """Test an API endpoint and save response."""
        response = await self._make_request(endpoint, params)

        # Save response to file
        output_file = self.output_dir / f"{save_as}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(response, f, indent=2)

        return response

    async def discover_ids(self):
        """Get example IDs for each main data type."""
        logger.info("Discovering example IDs...")

        # Get some Agaricus observations
        response = await self._make_request(
            "observations", {"names": "Agaricus", "detail": "low", "has_images": "true"}
        )
        if "results" in response:
            self.example_ids["observations"] = response["results"][:5]

            # Get associated images
            for obs_id in self.example_ids["observations"]:
                img_response = await self._make_request(
                    "images", {"observation_id": str(obs_id), "detail": "low"}
                )
                if "results" in img_response:
                    self.example_ids["images"].extend(img_response["results"][:2])

        # Get some name IDs
        response = await self._make_request(
            "names", {"children_of": "Agaricus", "detail": "low"}
        )
        if "results" in response:
            self.example_ids["names"] = response["results"][:5]

        # Get some location IDs
        response = await self._make_request("locations", {"detail": "low"})
        if "results" in response:
            self.example_ids["locations"] = response["results"][:5]

        # Save discovered IDs
        with open(self.output_dir / "example_ids.json", "w") as f:
            json.dump(self.example_ids, f, indent=2)

        logger.info("Discovered IDs: %s", self.example_ids)

    async def map_endpoints(self):
        """Map and test all relevant API endpoints."""
        # First discover some valid IDs
        await self.discover_ids()

        # Get API parameter documentation
        help_endpoints = [
            {"endpoint": name, "params": {"help": "1"}, "save_as": f"{name}_help"}
            for name in [
                "observations",
                "names",
                "images",
                "locations",
                "sequences",
                "external_links",
            ]
        ]

        # Test each help endpoint
        for endpoint_info in help_endpoints:
            logger.info(f"Getting help for: {endpoint_info['endpoint']}")
            await self.test_endpoint(
                endpoint_info["endpoint"],
                endpoint_info["params"],
                endpoint_info["save_as"],
            )

        # Test detailed data endpoints
        if self.example_ids["names"]:
            # Taxonomic data
            await self.test_endpoint(
                "names",
                {"children_of": "Agaricus", "detail": "high"},
                "names_children_high",
            )

            await self.test_endpoint(
                "names",
                {"id": str(self.example_ids["names"][0]), "detail": "high"},
                "name_detail_high",
            )

        if self.example_ids["observations"]:
            # Observation with images
            obs_id = str(self.example_ids["observations"][0])
            await self.test_endpoint(
                "observations",
                {"id": obs_id, "detail": "high"},
                "observation_detail_high",
            )

            # Images for observation
            await self.test_endpoint(
                "images",
                {"observation_id": obs_id, "detail": "high"},
                "images_for_obs_high",
            )

        if self.example_ids["locations"]:
            # Location details
            await self.test_endpoint(
                "locations",
                {"id": str(self.example_ids["locations"][0]), "detail": "high"},
                "location_detail_high",
            )

        # Test some special queries
        special_queries = [
            {
                "endpoint": "observations",
                "params": {
                    "location": "California",
                    "date": "2023",
                    "has_images": "true",
                    "detail": "high",
                },
                "save_as": "observations_filtered",
            },
            {
                "endpoint": "names",
                "params": {"rank": "Species", "has_images": "true", "detail": "high"},
                "save_as": "names_species_with_images",
            },
        ]

        for query in special_queries:
            logger.info(f"Testing special query: {query['save_as']}")
            await self.test_endpoint(
                query["endpoint"], query["params"], query["save_as"]
            )

        # Test sequences endpoint
        await self.test_endpoint(
            "sequences", {"name": "Agaricus", "detail": "high"}, "sequences_by_name"
        )

        # Test external links endpoint
        await self.test_endpoint(
            "external_links",
            {"name": "Agaricus xanthodermus", "detail": "high"},
            "external_links_by_name",
        )

        # Test external links for observation
        if self.example_ids["observations"]:
            obs_id = str(self.example_ids["observations"][0])
            await self.test_endpoint(
                "external_links",
                {"observation": obs_id, "detail": "high"},
                "external_links_for_obs",
            )

        # Test sequences with filters
        special_queries = [
            {
                "endpoint": "sequences",
                "params": {
                    "locus": "ITS",  # Internal Transcribed Spacer region
                    "detail": "high",
                },
                "save_as": "sequences_its",
            },
            {
                "endpoint": "external_links",
                "params": {"site": "Index Fungorum", "detail": "high"},
                "save_as": "external_links_index_fungorum",
            },
        ]

        for query in special_queries:
            logger.info(f"Testing special query: {query['save_as']}")
            await self.test_endpoint(
                query["endpoint"], query["params"], query["save_as"]
            )


async def main():
    """Main execution function."""
    config = DataConfig()
    output_dir = Path("api_responses")

    async with MOApiMapper(config, output_dir) as mapper:
        await mapper.map_endpoints()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
