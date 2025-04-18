"""Setup script to initialize required directories and files."""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

REQUIRED_DIRS = ["data", "api_cache", "temp", "logs"]

REQUIRED_FILES = {
    "logging.yaml": """
version: 1
formatters:
  simple:
    format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
handlers:
  console:
    class: logging.StreamHandler
    level: INFO
    formatter: simple
    stream: ext://sys.stdout
  file:
    class: logging.FileHandler
    level: INFO
    formatter: simple
    filename: logs/pipeline.log
root:
    level: INFO
    handlers: [console, file]
""",
    ".env": """
# MongoDB connection URI (replace with your actual URI)
MONGODB_URI=your_mongodb_uri_here
# Database name
DATABASE_NAME=mushroom_db
# Processing settings
BATCH_SIZE=1000
DEFAULT_DELIMITER=\t
# Comma-separated list of values to treat as NULL
NULL_VALUES=NULL,NA,None,""
DATE_FORMAT=%Y-%m-%d
MAX_RETRIES=3
RETRY_DELAY=5
CHUNK_SIZE=8192
""",
}


def setup_directories(base_path: Path) -> None:
    """Create required directories if they don't exist."""
    for dir_name in REQUIRED_DIRS:
        dir_path = base_path / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {dir_path}")


def setup_files(base_path: Path) -> None:
    """Create required files if they don't exist."""
    for filename, content in REQUIRED_FILES.items():
        file_path = base_path / filename
        if not file_path.exists():
            with open(file_path, "w") as f:
                f.write(content.strip())
            logger.info(f"Created file: {file_path}")


def main():
    """Main setup function."""
    logging.basicConfig(level=logging.INFO)

    # Get base path
    base_path = Path(__file__).parent.parent

    try:
        # Create directories
        setup_directories(base_path)

        # Create files
        setup_files(base_path)

        logger.info("Setup completed successfully")

    except Exception as e:
        logger.error(f"Setup failed: {e}")
        raise


if __name__ == "__main__":
    main()
