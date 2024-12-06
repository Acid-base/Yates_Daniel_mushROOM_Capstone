"""Data pipeline for combining CSV and API data."""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
import pandas as pd
from datetime import datetime, timedelta
import json
import shutil
from tqdm import tqdm

from config import DataConfig
from database import AsyncDatabase
from data_csv import DataProcessor
from api_mapper import MOApiMapper
from monitoring import measure_performance
from exceptions import DataProcessingError
from validation import validate_data

logger = logging.getLogger(__name__)

class PipelineProgress:
    """Track pipeline progress and enable recovery."""
    
    def __init__(self, progress_file: Path):
        self.progress_file = progress_file
        self.state: Dict[str, Any] = {
            "csv_tables_processed": set(),
            "api_enrichment": {
                "taxonomic": set(),
                "observations": set(),
                "external_links": set(),
                "sequences": set()
            },
            "last_update": None,
            "errors": [],
            "stats": {
                "total_records": 0,
                "processed_records": 0,
                "failed_records": 0,
                "start_time": None,
                "end_time": None
            }
        }
        self.load_progress()
    
    def load_progress(self):
        """Load progress from file."""
        if self.progress_file.exists():
            try:
                with open(self.progress_file) as f:
                    data = json.load(f)
                    # Convert JSON lists back to sets
                    self.state["csv_tables_processed"] = set(data["csv_tables_processed"])
                    for key in self.state["api_enrichment"]:
                        self.state["api_enrichment"][key] = set(data["api_enrichment"][key])
                    self.state["last_update"] = data["last_update"]
                    self.state["errors"] = data["errors"]
            except Exception as e:
                logger.error(f"Failed to load progress: {e}")
    
    def save_progress(self):
        """Save progress to file."""
        try:
            # Convert sets to lists for JSON serialization
            data = {
                "csv_tables_processed": list(self.state["csv_tables_processed"]),
                "api_enrichment": {
                    key: list(value)
                    for key, value in self.state["api_enrichment"].items()
                },
                "last_update": datetime.utcnow().isoformat(),
                "errors": self.state["errors"]
            }
            with open(self.progress_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save progress: {e}")
    
    def mark_csv_table_complete(self, table_name: str):
        """Mark a CSV table as processed."""
        self.state["csv_tables_processed"].add(table_name)
        self.save_progress()
    
    def mark_api_enrichment_complete(self, enrichment_type: str, item_id: int):
        """Mark an API enrichment as complete."""
        if enrichment_type in self.state["api_enrichment"]:
            self.state["api_enrichment"][enrichment_type].add(item_id)
            self.save_progress()
    
    def log_error(self, error: str, context: Dict[str, Any]):
        """Log an error with context."""
        self.state["errors"].append({
            "error": str(error),
            "context": context,
            "timestamp": datetime.utcnow().isoformat()
        })
        self.save_progress()
    
    def is_csv_table_processed(self, table_name: str) -> bool:
        """Check if a CSV table has been processed."""
        return table_name in self.state["csv_tables_processed"]
    
    def is_api_enrichment_complete(self, enrichment_type: str, item_id: int) -> bool:
        """Check if an API enrichment has been completed."""
        return (
            enrichment_type in self.state["api_enrichment"] and
            item_id in self.state["api_enrichment"][enrichment_type]
        )
    
    def update_stats(self, total: Optional[int] = None, processed: int = 0, failed: int = 0):
        """Update processing statistics."""
        if total is not None:
            self.state["stats"]["total_records"] = total
        self.state["stats"]["processed_records"] += processed
        self.state["stats"]["failed_records"] += failed
        self.save_progress()
    
    def get_progress_percentage(self) -> float:
        """Get overall progress percentage."""
        total = self.state["stats"]["total_records"]
        if total == 0:
            return 0.0
        return (self.state["stats"]["processed_records"] / total) * 100
    
    def get_eta(self) -> Optional[timedelta]:
        """Estimate time remaining based on progress."""
        if not self.state["stats"]["start_time"]:
            return None
            
        start = datetime.fromisoformat(self.state["stats"]["start_time"])
        now = datetime.utcnow()
        elapsed = now - start
        
        processed = self.state["stats"]["processed_records"]
        total = self.state["stats"]["total_records"]
        
        if processed == 0 or total == 0:
            return None
            
        rate = processed / elapsed.total_seconds()
        remaining_records = total - processed
        
        if rate == 0:
            return None
            
        seconds_remaining = remaining_records / rate
        return timedelta(seconds=int(seconds_remaining))

class DataPipeline:
    """Combined data pipeline for CSV and API data."""
    
    def __init__(self, config: DataConfig):
        self.config = config
        self.db = AsyncDatabase(config)
        self.csv_processor = DataProcessor(config)
        self.api_cache_dir = Path("api_cache")
        self.temp_dir = Path("temp")
        self.api_cache_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize progress tracking
        self.progress = PipelineProgress(Path("pipeline_progress.json"))
        
        # Track processed records
        self.processed_ids: Dict[str, Set[int]] = {
            "observations": set(),
            "names": set(),
            "locations": set(),
            "images": set()
        }
    
    async def validate_record(self, record: Dict[str, Any], schema_name: str) -> bool:
        """Validate a record against its schema."""
        try:
            # Basic schema validation
            if not validate_data(record, self.config.SCHEMAS[schema_name]):
                return False
            
            # Additional validation based on record type
            if schema_name == "observations":
                if not await self._validate_observation(record):
                    return False
            elif schema_name == "names":
                if not await self._validate_name(record):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Validation error for {schema_name} record {record.get('_id')}: {e}")
            return False
    
    async def _validate_observation(self, record: Dict[str, Any]) -> bool:
        """Validate observation-specific rules."""
        try:
            # Validate location if present
            if "location" in record:
                loc = record["location"]
                if "lat" in loc and "lng" in loc:
                    if not (-90 <= loc["lat"] <= 90 and -180 <= loc["lng"] <= 180):
                        return False
            
            # Validate date format
            if "when" in record:
                datetime.strptime(record["when"], "%Y-%m-%d")
            
            # Validate references
            if "name_id" in record:
                names_coll = self.db.get_collection("names")
                if not await names_coll.find_one({"_id": record["name_id"]}):
                    return False
            
            return True
            
        except Exception:
            return False
    
    async def _validate_name(self, record: Dict[str, Any]) -> bool:
        """Validate name-specific rules."""
        try:
            # Validate scientific name format
            if "text_name" in record:
                name = record["text_name"]
                if not name[0].isupper() or " " not in name:
                    return False
            
            # Validate rank
            if "rank" in record and record["rank"] not in range(1, 101):
                return False
            
            # Validate references
            if "synonym_id" in record and record["synonym_id"]:
                names_coll = self.db.get_collection("names")
                if not await names_coll.find_one({"_id": record["synonym_id"]}):
                    return False
            
            return True
            
        except Exception:
            return False
    
    @measure_performance
    async def initialize(self):
        """Initialize database connection and create indexes."""
        await self.db.connect()
        
        # Create indexes for each collection
        for collection, indexes in self.config.indexes.items():
            collection_obj = self.db.get_collection(collection)
            await self.db.ensure_indexes(collection_obj, indexes)
    
    @measure_performance
    async def process_csv_data(self):
        """Process all CSV data files."""
        logger.info("Starting CSV data processing...")
        
        # Process core tables first
        core_tables = ["names", "locations", "observations", "images"]
        for table in core_tables:
            if not self.progress.is_csv_table_processed(table):
                await self._process_csv_table(table)
        
        # Process relationship tables
        relation_tables = [
            "images_observations",
            "name_classifications",
            "name_descriptions"
        ]
        for table in relation_tables:
            if not self.progress.is_csv_table_processed(table):
                await self._process_csv_table(table)
            
        logger.info("CSV data processing complete")
    
    async def _process_csv_table(self, table_name: str):
        """Process a single CSV table."""
        logger.info(f"Processing {table_name}.csv")
        
        try:
            total_records = 0
            processed_records = 0
            failed_records = 0
            
            # Count total records first
            async for batch in self.csv_processor.process_file(table_name):
                total_records += len(batch)
            
            self.progress.update_stats(total=total_records)
            
            # Process records with progress bar
            with tqdm(total=total_records, desc=f"Processing {table_name}") as pbar:
                async for batch in self.csv_processor.process_file(table_name):
                    valid_records = []
                    
                    # Validate each record
                    for record in batch:
                        if await self.validate_record(record, table_name):
                            valid_records.append(record)
                            processed_records += 1
                        else:
                            failed_records += 1
                            self.progress.log_error(
                                "Validation failed",
                                {
                                    "table": table_name,
                                    "record_id": record.get("_id"),
                                    "stage": "validation"
                                }
                            )
                    
                    # Store IDs for API enrichment
                    if table_name in self.processed_ids:
                        self.processed_ids[table_name].update(
                            record["_id"] for record in valid_records
                        )
                    
                    # Insert valid records into MongoDB
                    if valid_records:
                        collection = self.db.get_collection(table_name)
                        await self.db.batch_upsert(collection, valid_records)
                    
                    # Update progress
                    pbar.update(len(batch))
                    self.progress.update_stats(processed=len(valid_records), failed=len(batch) - len(valid_records))
                    
                    # Show ETA
                    eta = self.progress.get_eta()
                    if eta:
                        pbar.set_postfix({"ETA": str(eta)})
            
            # Mark table as processed
            self.progress.mark_csv_table_complete(table_name)
            logger.info(f"Completed {table_name}: {processed_records} processed, {failed_records} failed")
                
        except Exception as e:
            self.progress.log_error(
                str(e),
                {"table": table_name, "stage": "csv_processing"}
            )
            raise DataProcessingError(f"Failed to process {table_name}: {str(e)}")
    
    @measure_performance
    async def enrich_with_api_data(self):
        """Enrich database records with API data."""
        logger.info("Starting API data enrichment...")
        
        async with MOApiMapper(self.config, self.api_cache_dir) as mapper:
            # Enrich taxonomic data
            await self._enrich_taxonomic_data(mapper)
            
            # Enrich observations with details
            await self._enrich_observations(mapper)
            
            # Get external references
            await self._enrich_external_links(mapper)
            
            # Get sequence data
            await self._enrich_sequence_data(mapper)
        
        logger.info("API data enrichment complete")
    
    async def _enrich_taxonomic_data(self, mapper: MOApiMapper):
        """Enrich species data with full taxonomic details."""
        names_coll = self.db.get_collection("names")
        
        for name_id in list(self.processed_ids["names"]):
            if self.progress.is_api_enrichment_complete("taxonomic", name_id):
                continue
                
            try:
                # Get high-detail API data
                api_data = await mapper.test_endpoint(
                    "names",
                    {"id": str(name_id), "detail": "high"},
                    f"name_{name_id}"
                )
                
                if "results" in api_data:
                    # Update database with enriched data
                    await names_coll.update_one(
                        {"_id": name_id},
                        {"$set": {
                            "api_data": api_data["results"][0],
                            "last_api_update": datetime.utcnow()
                        }}
                    )
                    self.progress.mark_api_enrichment_complete("taxonomic", name_id)
                    
            except Exception as e:
                self.progress.log_error(
                    str(e),
                    {"name_id": name_id, "stage": "taxonomic_enrichment"}
                )
                logger.error(f"Failed to enrich name {name_id}: {str(e)}")
    
    async def _enrich_observations(self, mapper: MOApiMapper):
        """Enrich observations with API details."""
        obs_coll = self.db.get_collection("observations")
        
        for obs_id in list(self.processed_ids["observations"]):
            if self.progress.is_api_enrichment_complete("observations", obs_id):
                continue
                
            try:
                # Get high-detail API data
                api_data = await mapper.test_endpoint(
                    "observations",
                    {"id": str(obs_id), "detail": "high"},
                    f"observation_{obs_id}"
                )
                
                if "results" in api_data:
                    # Update database with enriched data
                    await obs_coll.update_one(
                        {"_id": obs_id},
                        {"$set": {
                            "api_data": api_data["results"][0],
                            "last_api_update": datetime.utcnow()
                        }}
                    )
                    self.progress.mark_api_enrichment_complete("observations", obs_id)
                    
            except Exception as e:
                self.progress.log_error(
                    str(e),
                    {"observation_id": obs_id, "stage": "observation_enrichment"}
                )
                logger.error(f"Failed to enrich observation {obs_id}: {str(e)}")
    
    async def _enrich_external_links(self, mapper: MOApiMapper):
        """Get external references for species."""
        names_coll = self.db.get_collection("names")
        
        for name_id in list(self.processed_ids["names"]):
            if self.progress.is_api_enrichment_complete("external_links", name_id):
                continue
                
            try:
                # Get external links
                api_data = await mapper.test_endpoint(
                    "external_links",
                    {"name_id": str(name_id), "detail": "high"},
                    f"external_links_{name_id}"
                )
                
                if "results" in api_data:
                    # Update database with external links
                    await names_coll.update_one(
                        {"_id": name_id},
                        {"$set": {
                            "external_links": api_data["results"],
                            "last_links_update": datetime.utcnow()
                        }}
                    )
                    self.progress.mark_api_enrichment_complete("external_links", name_id)
                    
            except Exception as e:
                self.progress.log_error(
                    str(e),
                    {"name_id": name_id, "stage": "external_links_enrichment"}
                )
                logger.error(f"Failed to get external links for {name_id}: {str(e)}")
    
    async def _enrich_sequence_data(self, mapper: MOApiMapper):
        """Get DNA sequence data for species."""
        names_coll = self.db.get_collection("names")
        
        for name_id in list(self.processed_ids["names"]):
            if self.progress.is_api_enrichment_complete("sequences", name_id):
                continue
                
            try:
                # Get sequence data
                api_data = await mapper.test_endpoint(
                    "sequences",
                    {"name_id": str(name_id), "detail": "high"},
                    f"sequences_{name_id}"
                )
                
                if "results" in api_data:
                    # Update database with sequence data
                    await names_coll.update_one(
                        {"_id": name_id},
                        {"$set": {
                            "sequences": api_data["results"],
                            "last_sequence_update": datetime.utcnow()
                        }}
                    )
                    self.progress.mark_api_enrichment_complete("sequences", name_id)
                    
            except Exception as e:
                self.progress.log_error(
                    str(e),
                    {"name_id": name_id, "stage": "sequence_enrichment"}
                )
                logger.error(f"Failed to get sequences for {name_id}: {str(e)}")
    
    @measure_performance
    async def cleanup(self):
        """Clean up resources and temporary files."""
        try:
            # Close database connection
            await self.db.close()
            
            # Clean up temporary files
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
            
            # Clean up old API cache files (older than 7 days)
            if self.api_cache_dir.exists():
                current_time = datetime.utcnow()
                for cache_file in self.api_cache_dir.glob("*.json"):
                    file_age = current_time - datetime.fromtimestamp(cache_file.stat().st_mtime)
                    if file_age > timedelta(days=7):
                        cache_file.unlink()
            
            logger.info("Cleanup completed successfully")
            
        except Exception as e:
            logger.error(f"Cleanup failed: {str(e)}")
            raise
    
    async def generate_summary(self) -> Dict[str, Any]:
        """Generate a detailed pipeline summary."""
        summary = {
            "runtime": {
                "start": self.progress.state["stats"]["start_time"],
                "end": self.progress.state["stats"]["end_time"],
                "duration": None
            },
            "records": {
                "total": self.progress.state["stats"]["total_records"],
                "processed": self.progress.state["stats"]["processed_records"],
                "failed": self.progress.state["stats"]["failed_records"]
            },
            "csv_processing": {
                "tables_processed": list(self.progress.state["csv_tables_processed"]),
                "tables_failed": []
            },
            "api_enrichment": {
                "taxonomic": len(self.progress.state["api_enrichment"]["taxonomic"]),
                "observations": len(self.progress.state["api_enrichment"]["observations"]),
                "external_links": len(self.progress.state["api_enrichment"]["external_links"]),
                "sequences": len(self.progress.state["api_enrichment"]["sequences"])
            },
            "errors": {
                "total": len(self.progress.state["errors"]),
                "by_stage": {}
            },
            "data_integrity": await self.check_data_integrity()
        }
        
        # Calculate duration
        if summary["runtime"]["start"] and summary["runtime"]["end"]:
            start = datetime.fromisoformat(summary["runtime"]["start"])
            end = datetime.fromisoformat(summary["runtime"]["end"])
            summary["runtime"]["duration"] = str(end - start)
        
        # Group errors by stage
        for error in self.progress.state["errors"]:
            stage = error["context"].get("stage", "unknown")
            if stage not in summary["errors"]["by_stage"]:
                summary["errors"]["by_stage"][stage] = []
            summary["errors"]["by_stage"][stage].append(error)
        
        # Save summary to file
        summary_file = Path("pipeline_summary.json")
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        return summary
    
    async def check_data_integrity(self) -> Dict[str, Any]:
        """Perform data integrity checks."""
        integrity = {
            "reference_integrity": {
                "total_checked": 0,
                "issues_found": 0,
                "details": []
            },
            "data_consistency": {
                "total_checked": 0,
                "issues_found": 0,
                "details": []
            }
        }
        
        try:
            # Check observation references
            obs_coll = self.db.get_collection("observations")
            names_coll = self.db.get_collection("names")
            locations_coll = self.db.get_collection("locations")
            
            async for obs in obs_coll.find({}):
                integrity["reference_integrity"]["total_checked"] += 1
                
                # Check name reference
                if "name_id" in obs:
                    name = await names_coll.find_one({"_id": obs["name_id"]})
                    if not name:
                        integrity["reference_integrity"]["issues_found"] += 1
                        integrity["reference_integrity"]["details"].append({
                            "type": "missing_name_reference",
                            "observation_id": obs["_id"],
                            "name_id": obs["name_id"]
                        })
                
                # Check location reference
                if "location_id" in obs:
                    location = await locations_coll.find_one({"_id": obs["location_id"]})
                    if not location:
                        integrity["reference_integrity"]["issues_found"] += 1
                        integrity["reference_integrity"]["details"].append({
                            "type": "missing_location_reference",
                            "observation_id": obs["_id"],
                            "location_id": obs["location_id"]
                        })
            
            # Check name relationships
            async for name in names_coll.find({}):
                integrity["data_consistency"]["total_checked"] += 1
                
                # Check synonym references
                if "synonym_id" in name and name["synonym_id"]:
                    synonym = await names_coll.find_one({"_id": name["synonym_id"]})
                    if not synonym:
                        integrity["data_consistency"]["issues_found"] += 1
                        integrity["data_consistency"]["details"].append({
                            "type": "missing_synonym_reference",
                            "name_id": name["_id"],
                            "synonym_id": name["synonym_id"]
                        })
                
                # Check for circular synonyms
                if "synonym_id" in name and name["synonym_id"]:
                    visited = {name["_id"]}
                    current_id = name["synonym_id"]
                    while current_id:
                        if current_id in visited:
                            integrity["data_consistency"]["issues_found"] += 1
                            integrity["data_consistency"]["details"].append({
                                "type": "circular_synonym_reference",
                                "name_id": name["_id"],
                                "cycle": list(visited)
                            })
                            break
                        visited.add(current_id)
                        current = await names_coll.find_one({"_id": current_id})
                        if not current:
                            break
                        current_id = current.get("synonym_id")
            
        except Exception as e:
            logger.error(f"Data integrity check failed: {e}")
            integrity["error"] = str(e)
        
        return integrity
    
    def print_summary(self, summary: Dict[str, Any]):
        """Print a formatted summary to the console."""
        print("\n=== Pipeline Execution Summary ===\n")
        
        # Runtime
        print("Runtime:")
        print(f"  Start: {summary['runtime']['start']}")
        print(f"  End: {summary['runtime']['end']}")
        print(f"  Duration: {summary['runtime']['duration']}")
        
        # Record counts
        print("\nRecords:")
        print(f"  Total: {summary['records']['total']}")
        print(f"  Processed: {summary['records']['processed']}")
        print(f"  Failed: {summary['records']['failed']}")
        print(f"  Success Rate: {(summary['records']['processed'] / summary['records']['total'] * 100):.2f}%")
        
        # CSV Processing
        print("\nCSV Processing:")
        print(f"  Tables Processed: {len(summary['csv_processing']['tables_processed'])}")
        for table in summary['csv_processing']['tables_processed']:
            print(f"    - {table}")
        
        # API Enrichment
        print("\nAPI Enrichment:")
        for key, count in summary['api_enrichment'].items():
            print(f"  {key.title()}: {count}")
        
        # Errors
        print("\nErrors:")
        print(f"  Total Errors: {summary['errors']['total']}")
        for stage, errors in summary['errors']['by_stage'].items():
            print(f"  {stage}: {len(errors)}")
        
        # Data Integrity
        print("\nData Integrity:")
        ref_int = summary['data_integrity']['reference_integrity']
        data_cons = summary['data_integrity']['data_consistency']
        
        print("  Reference Integrity:")
        print(f"    Checked: {ref_int['total_checked']}")
        print(f"    Issues: {ref_int['issues_found']}")
        
        print("  Data Consistency:")
        print(f"    Checked: {data_cons['total_checked']}")
        print(f"    Issues: {data_cons['issues_found']}")
        
        print("\nDetailed summary saved to: pipeline_summary.json")

async def main():
    """Main execution function."""
    config = DataConfig()
    pipeline = DataPipeline(config)
    
    try:
        # Record start time
        pipeline.progress.state["stats"]["start_time"] = datetime.utcnow().isoformat()
        
        # Initialize pipeline
        await pipeline.initialize()
        
        # Process CSV data first
        await pipeline.process_csv_data()
        
        # Enrich with API data
        await pipeline.enrich_with_api_data()
        
        # Record end time
        pipeline.progress.state["stats"]["end_time"] = datetime.utcnow().isoformat()
        pipeline.progress.save_progress()
        
        # Generate and print summary
        summary = await pipeline.generate_summary()
        pipeline.print_summary(summary)
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        raise
    
    finally:
        await pipeline.cleanup()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main()) 