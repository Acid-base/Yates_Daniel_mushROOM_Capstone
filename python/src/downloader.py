"""Data downloader for Mushroom Observer CSV files."""

import asyncio
import aiohttp
import logging
from pathlib import Path
from typing import Optional, Dict

from src.config import DataConfig, MODataSource
from src.exceptions import FileProcessingError
from src.monitoring import measure_performance

logger = logging.getLogger(__name__)


class MODownloader:
    """Handles downloading of Mushroom Observer CSV files."""

    def __init__(self, config: DataConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Set up async context."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.DOWNLOAD_TIMEOUT)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up async context."""
        if self.session:
            await self.session.close()

    @measure_performance
    async def download_file(
        self, url: str, output_path: Path, force: bool = False
    ) -> bool:
        """
        Download a file from Mushroom Observer.

        Args:
            url: Source URL
            output_path: Where to save the file
            force: Whether to download even if file exists

        Returns:
            bool: True if file was downloaded, False if skipped
        """
        if not force and output_path.exists():
            logger.info(f"Skipping existing file: {output_path}")
            return False

        output_path.parent.mkdir(parents=True, exist_ok=True)

        for attempt in range(self.config.MAX_RETRIES):
            try:
                if not self.session:
                    raise FileProcessingError("No active session")

                async with self.session.get(url) as response:
                    if response.status != 200:
                        raise FileProcessingError(
                            f"Failed to download {url}: {response.status}"
                        )

                    with open(output_path, "wb") as f:
                        async for chunk in response.content.iter_chunked(
                            self.config.CHUNK_SIZE
                        ):
                            f.write(chunk)

                logger.info(f"Successfully downloaded: {output_path}")
                return True

            except Exception as e:
                logger.warning(f"Download attempt {attempt + 1} failed for {url}: {e}")
                if attempt < self.config.MAX_RETRIES - 1:
                    await asyncio.sleep(self.config.RETRY_DELAY)
                else:
                    raise FileProcessingError(
                        f"Failed to download {url} after {self.config.MAX_RETRIES} attempts"
                    )

    @measure_performance
    async def download_all(self, force: bool = False) -> Dict[str, Path]:
        """
        Download all Mushroom Observer CSV files.

        Args:
            force: Whether to force download even if files exist

        Returns:
            Dict mapping schema names to downloaded file paths
        """
        downloads = {
            "observations": MODataSource.OBSERVATIONS,
            "images_observations": MODataSource.IMAGES_OBSERVATIONS,
            "images": MODataSource.IMAGES,
            "names": MODataSource.NAMES,
            "name_classifications": MODataSource.NAME_CLASSIFICATIONS,
            "name_descriptions": MODataSource.NAME_DESCRIPTIONS,
            "locations": MODataSource.LOCATIONS,
            "location_descriptions": MODataSource.LOCATION_DESCRIPTIONS,
        }

        results = {}
        async with self:  # Use context manager for session management
            for schema_name, url in downloads.items():
                output_path = self.config.DATA_DIR / f"{schema_name}.csv"
                try:
                    downloaded = await self.download_file(url, output_path, force)
                    if downloaded or output_path.exists():
                        results[schema_name] = output_path
                except Exception as e:
                    logger.error(f"Failed to download {schema_name}: {e}")

        return results


async def download_mo_data(config: DataConfig, force: bool = False) -> Dict[str, Path]:
    """
    Download Mushroom Observer data files.

    Args:
        config: Application configuration
        force: Whether to force download even if files exist

    Returns:
        Dict mapping schema names to downloaded file paths
    """
    downloader = MODownloader(config)
    return await downloader.download_all(force)
