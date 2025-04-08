#!/usr/bin/env python
"""
Main entry point for mushROOM Capstone data pipeline.
This script configures and runs the complete data processing pipeline.
"""

import argparse
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Ensure src directory is on path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import required modules
from config import load_config, DataConfig
from data_pipeline import DataPipeline
from log_utils import get_logger

# Set up logger
logger = get_logger(__name__)


async def run_pipeline(pipeline: DataPipeline) -> bool:
    """Run the pipeline asynchronously."""
    try:
        success = await pipeline.run_pipeline_async()
        if not success:
            logger.error("Pipeline execution failed")
            return False
        return True
    finally:
        await pipeline.cleanup()


def main():
    """Main function to run data pipeline based on command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run mushROOM data processing pipeline."
    )
    parser.add_argument(
        "--config", type=str, default="config.yaml", help="Path to configuration file"
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        help="Directory containing CSV data files (overrides config)",
    )
    parser.add_argument(
        "--mongodb-uri", type=str, help="MongoDB connection URI (overrides config)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1000,
        help="Batch size for processing records (default: 1000)",
    )

    args = parser.parse_args()

    # Load configuration
    try:
        # Create DataConfig directly from environment variables
        config = DataConfig()

        # Override with config file if present
        if Path(args.config).exists():
            config_path = Path(args.config)
            if not config_path.is_absolute():
                config_path = Path(__file__).parent / args.config
            config = load_config(config_path)
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return 1

    # Override config with command line arguments if provided
    if args.data_dir:
        config.DATA_DIR = args.data_dir
    if args.mongodb_uri:
        config.MONGODB_URI = args.mongodb_uri
    if args.batch_size:
        config.BATCH_SIZE = args.batch_size

    # Initialize and run data pipeline
    try:
        pipeline = DataPipeline(config)
        success = asyncio.run(run_pipeline(pipeline))
        return 0 if success else 1
    except Exception as e:
        logger.error(f"Pipeline error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
