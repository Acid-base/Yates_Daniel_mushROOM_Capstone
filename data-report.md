# Mushroom Field Guide ETL Data Report

## 1. Overview

This document outlines the Extract-Transform-Load (ETL) process requirements for converting Mushroom Observer CSV datasets into a field guide-optimized MongoDB database. The final data structure focuses exclusively on mushroom species relevant for field identification, eliminating technical artifacts, redundant information, and optimizing for mobile usage.

## 2. Source Data Analysis

### 2.1 Source Files

Eight interrelated CSV files serve as source data:

1. **names.csv** (68,183 rows)
   - Core taxonomic information
   - `id`, `text_name`, `author`, `deprecated`, `correct_spelling_id`, `synonym_id`, `rank`
   - Contains various taxonomic ranks:
     * Species (rank=4): e.g., "Xylaria magnoliae"
     * Genus (rank=9): e.g., "Xeromphalina"
     * Kingdom (rank=14): e.g., "Fungi"
     * Group (rank=16): e.g., "Xylaria polymorpha group"
   - All examined samples have `deprecated=0`

2. **name_descriptions.csv** (6,368 rows)
   - Rich descriptive content for mushroom species
   - Contains multiple description fields: `general_description`, `diagnostic_description`, `distribution`, `habitat`, `look_alikes`, `uses`, `notes`, `refs`
   - Mixed formatting with three distinct patterns:
     * HTML links: `<a href="http://slimemold.uark.edu/martin.htm">http://slimemold.uark.edu/martin.htm</a>`
     * Textile links: `"http://naturalhistory.uga.edu/~GMNH/Mycoherb_Site/myxogal.htm":http://...`
     * Plain URLs: `http://www.mushroomexpert.com/panellus_stipticus.html`
   - Common names in format: `"Common Name: Plums and Custard"`
   - Notes field contains valuable taxonomic information (current names, synonyms, basionyms)
   - Embedded newlines represented as `\n`

3. **name_classifications.csv** (33,962 rows)
   - Hierarchical taxonomy classification
   - `name_id`, `domain`, `kingdom`, `phylum`, `class`, `order`, `family`
   - Missing values represented as empty strings, not NULL
   - All sample records include domain "Eukarya"
   - All mushroom samples belong to kingdom "Fungi"
   - Taxonomic levels include both Basidiomycota and Ascomycota phyla

4. **locations.csv** (26,697 rows)
   - Geographic location definitions
   - `id`, `name`, `north`, `south`, `east`, `west`, `high`, `low`
   - Location names follow "City, County, State, Country" format (e.g., "Albion, Mendocino Co., California, USA")
   - Contains geographic boundaries (north/south/east/west coordinates)
   - Elevation data (high/low) with some NULL values

5. **location_descriptions.csv** (1,160 rows)
   - Detailed location information
   - Fields: `id`, `location_id`, `source_type`, `source_name`, `gen_desc`, `ecology`, `species`, `notes`, `refs`
   - Rich habitat descriptions with embedded newlines (`\n`)
   - Contains scientific names of associated plants (e.g., "_Bursera simarouba_", "_Eugenia foetida_")
   - Detailed ecosystem descriptions (hammock, rockland, mangrove zones)

6. **observations.csv** (528,719 rows)
   - Mushroom sightings data
   - `id`, `name_id`, `when`, `location_id`, `lat`, `lng`, `alt`, `vote_cache`, `is_collection_location`, `thumb_image_id`
   - `vote_cache` indicates confidence of accurate ID (values in sample range from 1.92 to 2.83)
   - All coordinates (lat/lng/alt) are "NULL" in the sample data
   - All records have `is_collection_location=1`
   - Contains observation dates in ISO format (YYYY-MM-DD)

7. **images.csv** (1,725,855 rows)
   - Image metadata
   - `id`, `content_type`, `copyright_holder`, `license`, `ok_for_export`, `diagnostic`
   - All sample images are JPEG format (`content_type="image/jpeg"`)
   - Consistent copyright information ("Nathan Wilson" in samples)
   - Standard license format ("Creative Commons Wikipedia Compatible v3.0")
   - All samples have `ok_for_export=1` and `diagnostic=1`

8. **images_observations.csv** (1,637,370 rows)
   - Simple linking structure between images and observations
   - `image_id` and `observation_id` columns
   - In sample data, shows 1:1 relationship (one image per observation)

### 2.2 Key Data Quality Issues

1. **Description Field Quality**:
   - Mix of valuable content and URLs (sometimes entire fields are just URLs)
   - Complex mixed formatting with three distinct patterns:
     * HTML links: `<a href="http://slimemold.uark.edu/martin.htm">http://slimemold.uark.edu/martin.htm</a>`
     * Textile links: `"http://naturalhistory.uga.edu/~GMNH/Mycoherb_Site/myxogal.htm":http://...`
     * Plain URLs: `http://www.mushroomexpert.com/panellus_stipticus.html`
   - Embedded newlines represented as `\n` in multiple fields
   - Italicized scientific names in format `_Species name_`

2. **Common Name Extraction**:
   - Common names located in notes field with exact format: `"Common Name: Plums and Custard"`
   - Notes field also contains valuable taxonomic information (synonyms, basionyms)

3. **NULL Representation**:
   - "NULL" string in observations.csv (lat/lng/alt fields)
   - Empty strings in name_classifications.csv for missing taxonomy levels
   - Mix of empty fields and explicit "NULL" text

4. **Reference Handling**:
   - Rich but inconsistently formatted references in notes and refs fields
   - URL collections in lists (numbered 1., 2., etc.)
   - URLs embedded within descriptive text
   - Taxonomic references with detailed authority citation

5. **Species Selection**:
   - Must filter for Species rank (4) only
   - Group rank (16) records should be excluded
   - Filter by vote_cache for confident IDs (sample values range from 1.92 to 2.83)

## 3. Target Schema

The optimized field guide schema:

```json
{
  "_id": "<ObjectId>",
  "scientific_name": "String",
  "common_name": "String (if available)",
  "authority": "String",
  "classification": {
    "kingdom": "String",
    "phylum": "String",
    "class_name": "String",
    "order": "String",
    "family": "String"
  },
  "description": {
    "general": "String (clean text only)",
    "diagnostic": "String (clean text only)",
    "habitat": "String",
    "distribution": "String",
    "uses": "String",
    "look_alikes": "String"
  },
  "image": {
    "url": "String (640px version)",
    "copyright": "String (formatted attribution)",
    "license_url": "String"
  },
  "regional_distribution": {
    "countries": ["String"],
    "states": ["String"],
    "regions": ["String"]
  },
  "observation_data": {
    "count": "Number",
    "confidence": "Number (from vote_cache)",
    "first_observed": "Date",
    "last_observed": "Date"
  },
  "references": ["String (extracted URLs)"]
}
```

## 4. Transformation Requirements

### 4.1 Core Data Selection

1. **Filter Species Records**:
   - SELECT FROM names WHERE rank = 4 (Species) AND deprecated = 0
   - This provides accepted, current species names only

2. **Select Name Classifications**:
   - LEFT JOIN name_classifications ON names.id = name_classifications.name_id
   - Fill null taxonomy fields with appropriate defaults

3. **Select Descriptions**:
   - LEFT JOIN name_descriptions ON names.id = name_descriptions.name_id
   - Process text fields to extract clean content

### 4.2 Text Processing

1. **Description Cleaning**:
   - Remove HTML tags while preserving content
   - Convert Textile markup (`"link":URL`) to plain text
   - Extract embedded URLs to references array
   - Normalize newlines and whitespace
   - Reject description fields containing only addresses or invalid content

2. **Common Name Extraction**:
   - Parse notes field using regex: `"Common Name: ([^"]+)"`
   - Extract first match as common_name

3. **URL Extraction**:
   - Extract URLs from all description fields
   - Deduplicate and store in references array
   - Examples:
     - `http://www.mushroomexpert.com/panellus_stipticus.html`
     - `<a href="http://slimemold.uark.edu/martin.htm">http://slimemold.uark.edu/martin.htm</a>`
     - `"http://www.rogersmushrooms.com/gallery/DisplayBlock~bid~6883.asp"`

### 4.3 Image Selection

1. **Select Best Image**:
   - JOIN observations ON names.id = observations.name_id
   - JOIN images_observations ON observations.id = images_observations.observation_id
   - JOIN images ON images_observations.image_id = images.id
   - WHERE images.ok_for_export = 1
   - ORDER BY observations.vote_cache DESC
   - LIMIT 1 per species

2. **Image URL Creation**:
   - Format: `https://mushroomobserver.org/images/640/{image_id}.jpg`
   - Use 640px version for mobile-friendly display

3. **Copyright Formatting**:
   - Format: `© {copyright_holder}, {mapped_license_id}`

### 4.4 Location Processing

1. **Regional Distribution Extraction**:
   - Extract state, country from location names
   - Aggregate unique values by species
   - Format: Country > State > Region

2. **Observation Aggregation**:
   - Count total observations per species
   - Calculate average vote_cache as confidence score
   - Find earliest and latest observation dates

## 5. ETL Pipeline Implementation

### 5.1 Extraction Phase

```python
# Load all CSV files with appropriate options
names_df = pd.read_csv('data/names.csv', sep='\t', na_values=['NULL'])
name_descriptions_df = pd.read_csv('data/name_descriptions.csv', sep='\t',
                                  na_values=['NULL'], quoting=3, engine='python')
name_classifications_df = pd.read_csv('data/name_classifications.csv', sep='\t')
observations_df = pd.read_csv('data/observations.csv', sep='\t', na_values=['NULL'])
images_df = pd.read_csv('data/images.csv', sep='\t', na_values=['NULL'])
images_observations_df = pd.read_csv('data/images_observations.csv', sep='\t', na_values=['NULL'])
locations_df = pd.read_csv('data/locations.csv', sep='\t', na_values=['NULL'])
```

### 5.2 Transformation Phase

```python
# Filter for species rank only
species_df = names_df[(names_df['rank'] == 4) & (names_df['deprecated'] == 0)]

# Join with classifications
species_with_class = pd.merge(
    species_df,
    name_classifications_df,
    left_on='id',
    right_on='name_id',
    how='left'
)

# Process descriptions
def clean_description(text):
    """Clean HTML, Textile, extract URLs, normalize text"""
    if pd.isna(text) or not isinstance(text, str):
        return None, []

    # Extract URLs - using patterns found in sample data
    urls = []

    # Extract HTML links: <a href="http://url">text</a>
    html_links = re.findall(r'<a href="(https?://[^"]+)">[^<]+</a>', text)
    urls.extend(html_links)

    # Extract Textile links: "text":http://url
    textile_links = re.findall(r'"[^"]+"\s*:\s*(https?://\S+)', text)
    urls.extend(textile_links)

    # Extract bare URLs
    bare_urls = re.findall(r'(?<![">:])(https?://\S+)(?!["\'])', text)
    urls.extend(bare_urls)

    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)

    # Remove Textile links but keep the link text
    text = re.sub(r'"([^"]+)"\s*:https?://\S+', r'\1', text)

    # Normalize newlines
    text = text.replace('\\n', '\n')

    # Convert underscored scientific names to italics for better display
    text = re.sub(r'_([^_]+)_', r'\1', text)

    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    # Validate content (reject if just an address)
    if re.match(r'^\d+\s+[A-Za-z\s]+,\s+[A-Za-z\s]+,\s+[A-Z]{2}\s+\d+', text) or text.startswith('http'):
        return None, urls

    return text, list(set(urls))

# Process descriptions
def extract_field_data(row):
    """Extract clean description fields and references"""
    refs = []
    fields = {}

    # Process each description field
    for field in ['general_description', 'diagnostic_description',
                 'habitat', 'distribution', 'uses', 'look_alikes', 'notes']:
        if field in row and not pd.isna(row[field]):
            clean_text, urls = clean_description(row[field])
            fields[field.replace('_description', '')] = clean_text
            refs.extend(urls)

    # Extract common name with the exact format seen in samples
    if 'notes' in row and not pd.isna(row['notes']):
        # Exact pattern found in sample: "Common Name: Plums and Custard"
        common_name_match = re.search(r'"Common Name:\s+([^"]+)"', row['notes'])
        if common_name_match:
            fields['common_name'] = common_name_match.group(1).strip()

    # Extract synonyms and taxonomic information (optional enhancement)
    if 'notes' in row and not pd.isna(row['notes']):
        # Look for Current Name: pattern
        current_name_match = re.search(r'Current Name:\s*\n([^\n]+)', row['notes'])
        if current_name_match:
            fields['current_name'] = current_name_match.group(1).strip()

    return fields, list(set(refs))

# Join with descriptions and process
species_descriptions = pd.merge(
    species_with_class,
    name_descriptions_df,
    left_on='id',
    right_on='name_id',
    how='left'
)

# Find best images
observations_with_vote = observations_df[~observations_df['vote_cache'].isna()]
images_linked = pd.merge(
    images_observations_df,
    observations_with_vote,
    left_on='observation_id',
    right_on='id',
    how='inner'
)
images_with_data = pd.merge(
    images_linked,
    images_df,
    left_on='image_id',
    right_on='id',
    how='inner'
)

# Select best image per species
best_images = (images_with_data[images_with_data['ok_for_export'] == 1]
               .sort_values('vote_cache', ascending=False)
               .groupby('name_id')
               .first()
               .reset_index())

# Extract regional distribution
def extract_regions(location_names):
    """Extract countries, states from location names"""
    countries = set()
    states = set()

    for loc in location_names:
        parts = loc.split(', ')
        if len(parts) >= 2:
            country = parts[-1]
            countries.add(country)
            if country == 'USA' and len(parts) >= 3:
                state = parts[-2]
                states.add(state)

    return list(countries), list(states)
```

### 5.3 Document Creation

```python
def create_species_document(species_row, class_data, desc_data, image_data, location_data, obs_data):
    """Create final document for MongoDB"""
    # Basic species data
    doc = {
        "scientific_name": species_row['text_name'],
        "authority": species_row['author'] if not pd.isna(species_row['author']) else None,
        "classification": {
            "kingdom": class_data.get('kingdom'),
            "phylum": class_data.get('phylum'),
            "class_name": class_data.get('class'),
            "order": class_data.get('order'),
            "family": class_data.get('family')
        }
    }

    # Add description fields
    desc_fields, references = extract_field_data(desc_data)
    doc["description"] = {
        k: v for k, v in desc_fields.items()
        if k not in ['common_name'] and v is not None
    }

    # Add common name if found
    if 'common_name' in desc_fields:
        doc["common_name"] = desc_fields['common_name']

    # Add image if available
    if image_data is not None:
        doc["image"] = {
            "url": f"https://mushroomobserver.org/images/640/{image_data['image_id']}.jpg",
            "copyright": f"© {image_data['copyright_holder']}, {image_data['license']}",
            "license_url": map_license_url(image_data['license'])
        }

    # Add regional distribution
    if location_data is not None:
        countries, states = extract_regions(location_data['location_names'])
        doc["regional_distribution"] = {
            "countries": countries,
            "states": states
        }

    # Add observation data
    if obs_data is not None:
        doc["observation_data"] = {
            "count": obs_data['count'],
            "confidence": float(obs_data['avg_vote']) if 'avg_vote' in obs_data else None,
            "first_observed": obs_data['first_date'] if 'first_date' in obs_data else None,
            "last_observed": obs_data['last_date'] if 'last_date' in obs_data else None
        }

    # Add references
    if references:
        doc["references"] = references

    return doc
```

### 5.4 Loading Phase

```python
# Connect to MongoDB
client = pymongo.MongoClient("mongodb+srv://username:password@cluster.mongodb.net/")
db = client["mushroom_guide"]
collection = db["species"]

# Create indexes for efficient querying
collection.create_index("scientific_name")
collection.create_index("common_name")

# Insert documents
species_documents = []
for species_id in species_df['id']:
    # Gather all data for this species
    species_row = species_df[species_df['id'] == species_id].iloc[0]
    class_data = name_classifications_df[name_classifications_df['name_id'] == species_id].iloc[0] \
                if len(name_classifications_df[name_classifications_df['name_id'] == species_id]) > 0 else {}
    desc_data = name_descriptions_df[name_descriptions_df['name_id'] == species_id].iloc[0] \
                if len(name_descriptions_df[name_descriptions_df['name_id'] == species_id]) > 0 else {}
    image_data = best_images[best_images['name_id'] == species_id].iloc[0] \
                if len(best_images[best_images['name_id'] == species_id]) > 0 else None

    # Create document
    doc = create_species_document(species_row, class_data, desc_data, image_data, location_data, obs_data)
    species_documents.append(doc)

# Bulk insert
collection.insert_many(species_documents)
```

## 6. Final Notes & Recommendations

1. **Image Quality Control**:
   - Some species may lack high-quality images
   - Set minimum vote_cache threshold (e.g., > 2.0) for image selection

2. **Description Validation**:
   - Implement content validation checks
   - Flag species with missing critical fields

3. **Data Completeness**:
   - Some species may have minimal information
   - Consider filtering out species with insufficient data

4. **Text Normalization**:
   - Create comprehensive text cleaning functions
   - Handle all encountered formatting variants

5. **Performance Optimization**:
   - Process large files in chunks
   - Consider parallel processing for text cleaning

This report provides complete guidance for implementing an ETL pipeline that transforms raw Mushroom Observer data into a streamlined, field guide-optimized MongoDB database suitable for mobile applications. The pipeline focuses on extracting valuable identification information while eliminating technical artifacts and redundant data.
