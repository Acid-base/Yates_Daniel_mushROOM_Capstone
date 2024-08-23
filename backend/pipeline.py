import csv
import json
import requests
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
import logging
import sys
import os
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import hashlib
from typing import Dict, List, Any
from functools import lru_cache
Load environment variables

load_dotenv()
--- Logging Configuration ---

logging.basicConfig(
level=logging.INFO,
format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
handlers=[
logging.FileHandler("mushroom_processor.log"),
logging.StreamHandler(sys.stdout)
]
)
logger = logging.getLogger("MushroomDataProcessor")
--- Configuration ---

MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
DATABASE_NAME = os.getenv('DATABASE_NAME', 'mushroom_db')
CSV_URLS = json.loads(os.getenv('CSV_URLS', '[]'))
API_ENDPOINTS = json.loads(os.getenv('API_ENDPOINTS', '{}'))
MAX_RETRIES = int(os.getenv('MAX_RETRIES', 3))
API_RATE_LIMIT = float(os.getenv('API_RATE_LIMIT', 0.2))
LAST_UPDATED_AT = os.getenv('LAST_UPDATED_AT')
--- Helper Functions ---

def retry_with_backoff(func):
def wrapper(*args, **kwargs):
for attempt in range(MAX_RETRIES):
try:
return func(*args, **kwargs)
except requests.exceptions.RequestException as e:
if attempt == MAX_RETRIES - 1:
logger.error(f"Max retries reached for {func.name}: {e}")
raise
wait_time = 2 ** attempt
logger.warning(f"Attempt {attempt + 1} failed. Retrying in {wait_time} seconds...")
time.sleep(wait_time)
return wrapper

@retry_with_backoff
def download_csv(url: str) -> str:
response = requests.get(url)
response.raise_for_status()
filename = url.split("/")[-1]
with open(filename, "wb") as f:
f.write(response.content)
logger.info(f"Downloaded {filename}")
return filename

def csv_to_json(csv_filename: str) -> List[Dict[str, Any]]:
try:
with open(csv_filename, 'r', encoding='utf-8') as csvfile:
reader = csv.DictReader(csvfile)
return list(reader)
except Exception as e:
logger.error(f"Error converting {csv_filename} to JSON: {e}")
return []

@retry_with_backoff
def fetch_api_data(endpoint: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
all_data = []
page = 1
while True:
time.sleep(1 / API_RATE_LIMIT) # Rate limiting
request_params = {'page': page, **(params or {})}
response = requests.get(endpoint, params=request_params)
response.raise_for_status()
data = response.json()

      
all_data.extend(data.get('results', []))
    if data.get('current_page', 1) >= data.get('total_pages', 1):
        return all_data
    page += 1

    

Use code with caution.

def clean_json_data(json_data: List[Dict[str, Any]], data_type: str) -> List[Dict[str, Any]]:
cleaned_data = []
for item in json_data:
try:
cleaned_item = clean_item(item, data_type)
if cleaned_item and validate_item(cleaned_item, data_type):
cleaned_data.append(cleaned_item)
except Exception as e:
logger.error(f"Error cleaning {data_type} item: {e}")
return cleaned_data

def clean_item(item: Dict[str, Any], data_type: str) -> Dict[str, Any]:
if data_type == 'observations':
return clean_observation(item)
elif data_type == 'images':
return clean_image(item)
elif data_type == 'locations':
return clean_location(item)
elif data_type == 'location_descriptions':
return clean_location_description(item)
else:
return item

def clean_observation(item: Dict[str, Any]) -> Dict[str, Any]:
cleaned = item.copy()
cleaned['date'] = parse_date(item.get('when'))
cleaned['latitude'] = float(item.get('lat', 0))
cleaned['longitude'] = float(item.get('lng', 0))
cleaned['altitude'] = float(item.get('alt', 0))
cleaned['is_collection_location'] = bool(item.get('is_collection_location'))
cleaned['notes'] = clean_text(item.get('notes', ''))

      
if not (-90 <= cleaned['latitude'] <= 90) or not (-180 <= cleaned['longitude'] <= 180):
    logger.warning(f"Invalid latitude/longitude in observation: {item}")
    return None

return cleaned

    

Use code with caution.

def clean_image(item: Dict[str, Any]) -> Dict[str, Any]:
cleaned = item.copy()
cleaned['created_at'] = parse_date(item.get('created_at'))
cleaned['updated_at'] = parse_date(item.get('updated_at'))
cleaned['notes'] = clean_text(item.get('notes', ''))
return cleaned

def clean_location(item: Dict[str, Any]) -> Dict[str, Any]:
cleaned = item.copy()
cleaned['coordinates'] = {
"type": "Point",
"coordinates": [float(item.get('lng', 0)), float(item.get('lat', 0))]
}
return cleaned

def clean_location_description(item: Dict[str, Any]) -> Dict[str, Any]:
cleaned = item.copy()
cleaned['description'] = clean_text(item.get('gen_desc', ''))
return cleaned

def validate_item(item: Dict[str, Any], data_type: str) -> bool:
required_fields = {
'observations': ['id', 'name_id', 'location_id', 'date'],
'images': ['id', 'url'],
'names': ['id', 'text_name'],
'name_classifications': ['name_id', 'classification'],
'name_descriptions': ['name_id'],
'locations': ['id', 'name'],
'location_descriptions': ['location_id']
}
return all(item.get(field) for field in required_fields.get(data_type, []))

@lru_cache(maxsize=1000)
def parse_classification(classification_str: str) -> Dict[str, str]:
try:
ranks = classification_str.split("|")
if len(ranks) == 7:
return {
"kingdom": ranks[0],
"phylum": ranks[1],
"class": ranks[2],
"order": ranks[3],
"family": ranks[4],
"genus": ranks[5],
"species": ranks[6]
}
else:
logger.warning(f"Unexpected classification format: {classification_str}")
return {}
except Exception as e:
logger.error(f"Error parsing classification: {e}")
return {}

def clean_text(text: str) -> str:
return str(text).strip().lower() if text is not None else ""

def parse_date(date_str: str) -> datetime:
if not date_str:
return None
try:
return datetime.strptime(date_str, "%Y-%m-%d")
except ValueError as e:
logger.warning(f"Error parsing date {date_str}: {e}")
return None

def generate_hash(data: Dict[str, Any]) -> str:
return hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()
--- Data Processing Functions ---

def process_csv_data() -> Dict[str, List[Dict[str, Any]]]:
json_data = {}
with ThreadPoolExecutor() as executor:
future_to_url = {executor.submit(download_csv, url): url for url in CSV_URLS}
for future in as_completed(future_to_url):
url = future_to_url[future]
filename = future.result()
if filename:
data_type = filename.split('.')[0]
raw_json = csv_to_json(filename)
json_data[data_type] = clean_json_data(raw_json, data_type)
logger.info(f"Processed CSV data for {data_type}")
return json_data

def process_api_data(last_updated_at: datetime = None) -> Dict[str, List[Dict[str, Any]]]:
json_data = {}
for data_type, endpoint_template in API_ENDPOINTS.items():
logger.info(f"Processing API data for {data_type}")
endpoint = endpoint_template.format(api_version='api2')
params = {'since': last_updated_at.isoformat()} if last_updated_at else {}
api_data = fetch_api_data(endpoint, params)
if api_data:
cleaned_api_data = clean_json_data(api_data, data_type)
json_data[data_type] = cleaned_api_data
logger.info(f"Processed {len(cleaned_api_data)} records from API for {data_type}")
return json_data

def create_lookup_dictionaries(json_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Dict[str, Any]]:
return {
'names': {item['id']: item for item in json_data.get('names', [])},
'name_classifications': {item['name_id']: item for item in json_data.get('name_classifications', [])},
'name_descriptions': {item['name_id']: item for item in json_data.get('name_descriptions', [])},
'locations': {item['id']: item for item in json_data.get('locations', [])},
'location_descriptions': {item['location_id']: item for item in json_data.get('location_descriptions', [])}
}

def insert_images(db, json_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, ObjectId]:
image_id_map = {}
for image in json_data.get('images', []):
try:
image_doc = {
"url": image.get('url', ''),
"notes": image.get('notes', ''),
"created_at": image.get('created_at'),
"updated_at": image.get('updated_at')
}
image_hash = generate_hash(image_doc)
existing_image = db.images.find_one({"hash": image_hash})
if existing_image:
image_id_map[image['id']] = existing_image['_id']
else:
image_doc['hash'] = image_hash
result = db.images.insert_one(image_doc)
image_id_map[image['id']] = result.inserted_id
except Exception as e:
logger.error(f"Error inserting image {image.get('id')}: {e}")
return image_id_map

def process_mushroom_data(db, json_data: Dict[str, List[Dict[str, Any]]], lookup_dicts: Dict[str, Dict[str, Any]], image_id_map: Dict[str, ObjectId]):
for observation in json_data.get('observations', []):
try:
name_id = observation['name_id']
name_data = lookup_dicts['names'].get(name_id, {})
classification_data = lookup_dicts['name_classifications'].get(name_id, {})
description_data = lookup_dicts['name_descriptions'].get(name_id, {})
location_id = observation['location_id']
location_data = lookup_dicts['locations'].get(location_id, {})
location_description_data = lookup_dicts['location_descriptions'].get(location_id, {})

      
mushroom_doc = create_mushroom_document(observation, name_data, classification_data, description_data, location_data, location_description_data, image_id_map)
        
        # Deduplication
        mushroom_hash = generate_hash(mushroom_doc)
        existing_mushroom = db.mushrooms.find_one({"hash": mushroom_hash})
        if existing_mushroom:
            db.mushrooms.update_one(
                {"_id": existing_mushroom['_id']},
                {"$addToSet": {"observations": mushroom_doc['observations'][0]}}
            )
            logger.info(f"Updated existing mushroom document for {mushroom_doc['name']}")
        else:
            mushroom_doc['hash'] = mushroom_hash
            db.mushrooms.insert_one(mushroom_doc)
            logger.info(f"Inserted new mushroom document for {mushroom_doc['name']}")
        
    except Exception as e:
        logger.error(f"Error processing observation {observation.get('id')}: {e}")

    

Use code with caution.

def create_mushroom_document(observation, name_data, classification_data, description_data, location_data, location_description_data, image_id_map):
return {
"name": name_data.get('text_name', ''),
"commonNames": name_data.get('common_names', '').split(', '),
"classification": parse_classification(classification_data.get('classification', '')),
"description": {
"general": description_data.get('gen_desc', ''),
"diagnostic": description_data.get('diag_desc', ''),
"distribution": description_data.get('distribution', ''),
"habitat": description_data.get('habitat', ''),
"lookalikes": description_data.get('look_alikes', '').split(', '),
"uses": description_data.get('uses', ''),
"notes": description_data.get('notes', '')
},
"images": [
image_id_map[image_id]
for image_id in observation.get('image_ids', '').split()
if image_id in image_id_map
],
"observations": [{
"date": observation['date'],
"latitude": observation['latitude'],
"longitude": observation['longitude'],
"altitude": observation['altitude'],
"is_collection_location": observation['is_collection_location'],
"notes": observation['notes']
}],
"location": {
"name": location_data.get('name', ''),
"coordinates": location_data.get('coordinates', {}),
"description": location_description_data.get('description', '')
}
}
--- Database Operations ---

def get_database_connection():
client = MongoClient(MONGODB_URI)
return client[DATABASE_NAME]
--- Main Execution ---

def main():
global LAST_UPDATED_AT
logger.info("Starting mushroom data processing")

      
db = get_database_connection()

# Initial CSV data processing
if not LAST_UPDATED

    

Use code with caution.
... (previous code remains the same)
--- Main Execution ---

def main():
global LAST_UPDATED_AT
logger.info("Starting mushroom data processing")

      
db = get_database_connection()

# Initial CSV data processing
if not LAST_UPDATED_AT:
    logger.info("Performing initial data load from CSV files.")
    csv_data = process_csv_data()
    lookup_dicts = create_lookup_dictionaries(csv_data)
    image_id_map = insert_images(db, csv_data)
    process_mushroom_data(db, csv_data, lookup_dicts, image_id_map)
    LAST_UPDATED_AT = datetime.utcnow()
    update_last_updated_timestamp(LAST_UPDATED_AT)

# API data processing for updates
logger.info("Fetching updates from API.")
api_data = process_api_data(LAST_UPDATED_AT)

if api_data:
    lookup_dicts = create_lookup_dictionaries(api_data)
    image_id_map = insert_images(db, api_data)
    process_mushroom_data(db, api_data, lookup_dicts, image_id_map)
    LAST_UPDATED_AT = datetime.utcnow()
    update_last_updated_timestamp(LAST_UPDATED_AT)

logger.info("Data processing completed.")

    

Use code with caution.

def update_last_updated_timestamp(timestamp):
# Update the LAST_UPDATED_AT value in the .env file
with open('.env', 'r') as file:
lines = file.readlines()

      
with open('.env', 'w') as file:
    for line in lines:
        if line.startswith('LAST_UPDATED_AT='):
            file.write(f'LAST_UPDATED_AT={timestamp.isoformat()}\n')
        else:
            file.write(line)

    

Use code with caution.

if name == "main":
main()
--- Additional Improvements ---
1. Add data validation and cleaning functions

def validate_coordinates(lat, lon):
return -90 <= lat <= 90 and -180 <= lon <= 180
2. Implement more robust error handling

class DataProcessingError(Exception):
pass

def safe_process(func):
def wrapper(*args, **kwargs):
try:
return func(*args, **kwargs)
except Exception as e:
logger.error(f"Error in {func.name}: {e}")
raise DataProcessingError(f"Failed to process data in {func.name}")
return wrapper
3. Add a function to handle database migrations

def perform_database_migrations(db):
# Check the current database version and apply necessary migrations
current_version = db.metadata.find_one({"key": "schema_version"})
if not current_version:
# Apply initial migration
db.mushrooms.create_index([("name", 1)], unique=True)
db.mushrooms.create_index([("location.coordinates", "2dsphere")])
db.metadata.insert_one({"key": "schema_version", "value": 1})
# Add more migrations as needed
4. Implement a simple caching mechanism

from functools import lru_cache

@lru_cache(maxsize=1000)
def get_mushroom_by_name(db, name):
return db.mushrooms.find_one({"name": name})
5. Add a function to perform periodic database maintenance

def perform_database_maintenance(db):
# Remove duplicate entries
duplicates = db.mushrooms.aggregate([
{"$group": {
"_id": "$name",
"count": {"$sum": 1},
"ids": {"$push": "$_id"}
}},
{"$match": {
"count": {"$gt": 1}
}}
])

      
for duplicate in duplicates:
    # Keep the first document and remove others
    db.mushrooms.delete_many({"_id": {"$in": duplicate["ids"][1:]}})

# Optionally, compact the database to reclaim space
db.command("compact", "mushrooms")

    

Use code with caution.
6. Implement a simple API for querying the database

from flask import Flask, jsonify, request

app = Flask(name)

@app.route('/api/mushroom', methods=['GET'])
def get_mushroom():
name = request.args.get('name')
if not name:
return jsonify({"error": "Name parameter is required"}), 400

      
mushroom = get_mushroom_by_name(db, name)
if not mushroom:
    return jsonify({"error": "Mushroom not found"}), 404

return jsonify(mushroom)

    

Use code with caution.

@app.route('/api/mushrooms/nearby', methods=['GET'])
def get_nearby_mushrooms():
lat = float(request.args.get('lat'))
lon = float(request.args.get('lon'))
max_distance = float(request.args.get('distance', 10000)) # Default to 10km

      
if not validate_coordinates(lat, lon):
    return jsonify({"error": "Invalid coordinates"}), 400

nearby_mushrooms = db.mushrooms.find({
    "location.coordinates": {
        "$near": {
            "$geometry": {
                "type": "Point",
                "coordinates": [lon, lat]
            },
            "$maxDistance": max_distance
        }
    }
})

return jsonify(list(nearby_mushrooms))

    

Use code with caution.

if name == "main":
db = get_database_connection()
perform_database_migrations(db)
main()
perform_database_maintenance(db)
app.run(debug=True)
