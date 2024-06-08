// backend/scripts/import.js
// path: /backend/scripts/import.js
// This script imports data from CSV files into our MongoDB database. 
// It's an essential step in preparing our application for deployment.

// --- 1. Require Necessary Modules ---

const mongoose = require('mongoose');   // Mongoose for interacting with our MongoDB database
const fs = require('fs');              // Node.js file system module for reading our CSV files
const csv = require('fast-csv');      // Fast-csv for efficient CSV parsing
const models = require('../models/index'); // Our Mongoose models (representing database collections)
const cliProgress = require('cli-progress'); // For progress bars

// --- 2. Database Connection ---

async function importCSV() {
  try {
    // Connect to our MongoDB database (make sure it's running!)
    await mongoose.connect('mongodb://localhost:27017/mushroom_app', {
    });
    console.log('Connected to MongoDB!');

    // --- 3. License Lookup Table  --- 

    // Optimization: Images reference licenses. To avoid querying the database for each image 
    // during the import, we'll create a lookup table to store license data after importing 
    // the 'licenses.csv' file.

    const licensesLookup = {};  // Initialize an empty object to store our license lookup table
    await importData('./data/licenses.csv', licensesLookup); // Import licenses and populate the lookup table 

    // --- 4. Define Import Order and Configuration --- 

    // We need to import files in a specific order to handle relationships between data. 
    // For example, we import 'licenses.csv' first because 'images.csv' references licenses.
    const importConfig = [
      { 
        file: './data/images.csv',         // Path to the CSV file
        delimiter: ';',                // Delimiter used in this CSV (';' in this case)
        lookupTable: licensesLookup    // Pass the licenses lookup table for this file
      },
      { 
        file: './data/names.csv', 
        delimiter: ' '                 // Delimiter is a space for this file
      },
      { 
        file: './data/locations.csv', 
        delimiter: ' ' 
      },
      { 
        file: './data/observations.csv' 
      },
      { 
        file: './data/images_observations.csv' 
      },
      { 
        file: './data/location_descriptions.csv' 
      },
      { 
        file: './data/name_classifications.csv', 
        delimiter: ' ' 
      },
      { 
        file: './data/name_descriptions.csv', 
        delimiter: ' ' 
      },
      { 
        file: './data/users.csv' // Added for users
      },
    ];

    // --- 5. Execute Imports ---

    // Loop through the import configuration and import each file
    for (const config of importConfig) {
      await importData(config.file, config.lookupTable || null, config.delimiter);
    }

    // --- 6. Data Integrity Checks (Example) ---

    // It's good practice to add checks to make sure our data is imported correctly. 
    // Here's an example that checks if all images have associated licenses:

    // await checkImageLicenseReferences(); // Uncomment after implementing this function

    // --- 7. Completion & Disconnect ---
    console.log('\nAll data import operations completed successfully!');
    await mongoose.disconnect(); 
    console.log('Disconnected from MongoDB!');

  } catch (error) {
    console.error('Error during data import:', error);
    process.exit(1); // Exit with an error code
  }
}

// --- Generic Import Function ---

// This function handles the import logic for a single CSV file. 
// It's reusable and helps keep our code organized.

async function importData(filePath, lookupTable = null, delimiter = ',') {
  const fileName = filePath.split('/').pop(); // Get the filename from the file path 
  console.log(`\n----- Importing ${fileName} -----`);
  
  try {
    // --- a. Read and Parse the CSV --- 
    const data = [];                // Array to store the parsed data
    const stream = fs.createReadStream(filePath); // Create a readable stream from the CSV file
    const csvStream = csv.parse({ headers: true, skipLines: 0, delimiter }); // Configure the CSV parser
    let rowCount = 0;
    let skippedRows = 0;

    // --- Progress Bar ---
    const progressBar = new cliProgress.SingleBar({
      format: '{bar} {percentage}% | {value}/{total} {filename} | ETA: {eta}s',
      barCompleteChar: '\u2588', 
      barIncompleteChar: '\u2591',
      hideCursor: true,
    }, cliProgress.Presets.shades_classic);
    
    // Get total lines for progress (could be optimized if slow)
    const totalLines = (await fs.promises.readFile(filePath, 'utf-8')).split('\n').length - 1;
    progressBar.start(totalLines, 0, { filename: fileName });

    // --- b. Process Each Row in the CSV --- 

    csvStream
      .on('data', (row) => {
        rowCount++;
        progressBar.update(rowCount, { filename: fileName });
        // Call the mapDataToModel function (defined below) to map CSV data to our Mongoose model
        // This function will handle data type conversions, validations, and using the lookup table.
        const formattedRow = mapDataToModel(fileName, row, lookupTable); 

        // If the data mapping is successful, add the formatted row to our data array
        if (formattedRow) {
          data.push(formattedRow);
        } else {
          skippedRows++;
        }
      })
      .on('end', async () => { // When the CSV parsing is complete
        progressBar.stop();
        try {
          if (data.length > 0) { 
            // Get the Mongoose model name from the filename (e.g., 'images.csv' -> 'Image')
            const modelName = getModelName(fileName); 

            // Make sure the model exists
            if (modelName) { 
              // Insert the data into the MongoDB collection
              console.log(`\nInserting ${data.length} records into ${modelName}...`);
              const result = await models[modelName].insertMany(data, { ordered: false, rawResult: true });
              console.log(`Inserted ${result.insertedCount} ${modelName} records.`); 
              if (skippedRows > 0) {
                console.log(`Skipped ${skippedRows} invalid records in ${fileName}.`);
              }
            } else {
              console.warn(`Model not found for ${fileName}. Skipping import.`);
            }
          }
        } catch (error) {
          handleImportError(error, fileName);
        }
      });

    // Pipe the CSV stream to the parser to start the process
    stream.pipe(csvStream);

  } catch (error) {
    console.error(`Error importing ${fileName}:`, error);
  }
}


// --- Helper Functions ---

// Maps CSV data to our Mongoose models, handles data types, validation, and lookups
// (You'll need to implement this based on your CSV structure and models)
function mapDataToModel(fileName, row, lookupTable) {
  switch (fileName) {
    case 'images.csv':
      return {
        id: parseInt(row.id),
        content_type: row.content_type.toLowerCase(),
        copyright_holder: row.copyright_holder ? row.copyright_holder.trim() : null,
        ok_for_export: row.ok_for_export === '1',
        diagnostic: row.diagnostic === '1', 
        license: lookupTable[row.license] || null,  // Use lookup table, default to null
        image_url: row.image_url
      };
    case 'licenses.csv':
      const licenseData =  {
          id: parseInt(row.id),
          displayName: row.displayName
        };
      // Populate the lookup table
      lookupTable[licenseData.displayName] = licenseData.id; 
      return licenseData;
    case 'names.csv':
      return {
        _id: parseInt(row.id),
        text_name: row.text_name,
        author: row.author,
        deprecated: row.deprecated === '1', 
        correct_spelling_id: parseInt(row.correct_spelling_id), 
        synonym_id: parseInt(row.synonym_id), 
        rank: parseInt(row.rank)
      };
    case 'locations.csv':
      return {
        _id: parseInt(row.id),
        name: row.name,
        area: {
          type: 'Polygon',
          coordinates: [ 
            [
              [parseFloat(row.west), parseFloat(row.south)],
              [parseFloat(row.east), parseFloat(row.south)],
              [parseFloat(row.east), parseFloat(row.north)],
              [parseFloat(row.west), parseFloat(row.north)],
              [parseFloat(row.west), parseFloat(row.south)] 
            ]
          ]
        },
        high: parseFloat(row.high),
        low: parseFloat(row.low)
      };
    case 'observations.csv':
      return {
        id: parseInt(row.id),
        name: row.name,
        scientific_name: row.scientific_name,
        when: new Date(row.when), 
        lat: parseFloat(row.lat),
        lng: parseFloat(row.lng),
        where: row.where,
        user_id: parseInt(row.user_id),
        thumb_image_id: parseInt(row.thumb_image_id),
        family: row.family,
        genus: row.genus,
        type: row.type
      };
    case 'images_observations.csv':
      return {
        observation: parseInt(row.observation_id),
        image: parseInt(row.image_id)
      };
    case 'location_descriptions.csv':
      return {
        _id: parseInt(row.id), 
        location: parseInt(row.location_id),
        source_type: row.source_type,
        source_name: row.source_name,
        gen_desc: row.gen_desc,
        ecology: row.ecology,
        species: row.species,
        notes: row.notes,
        refs: row.refs
      };
    case 'name_classifications.csv':
      return {
        name: parseInt(row.name_id), 
        domain: row.domain,
        kingdom: row.kingdom,
        phylum: row.phylum,
        class: row.class,
        order: row.order,
        family: row.family
      };
    case 'name_descriptions.csv':
      return {
        _id: parseInt(row.id), 
        name: parseInt(row.name_id), 
        source_type: row.source_type,
        source_name: row.source_name,
        general_description: row.general_description,
        diagnostic_description: row.diagnostic_description,
        distribution: row.distribution,
        habitat: row.habitat,
        look_alikes: row.look_alikes,
        uses: row.uses,
        notes: row.notes,
        refs: row.refs
      };
    case 'users.csv':
      return {
        name: row.name,
        email: row.email,
        // Add more fields if you have them in your CSV
      };

    default:
      console.warn(`Data mapping not defined for ${fileName}`);
      return null; 
  }
}

// Extracts the Mongoose model name from the CSV filename 
function getModelName(fileName) {
  const nameParts = fileName.replace('.csv', '').split('_');
  return nameParts.map(part => part.charAt(0).toUpperCase() + part.slice(1)).join('');
}

// Handles errors during the import process
function handleImportError(error, fileName) {
  if (error.code === 11000) {
    const numDuplicates = error.writeErrors.length;
    console.log(`Skipped ${numDuplicates} duplicate entries in ${fileName}.`);
  } else {
    console.error(`Error inserting data from ${fileName}:`, error);
    // throw error; // Uncomment if you want the import to stop on any error
  }
}

// Example Data Integrity Check (Optional - Implement as needed)

async function checkImageLicenseReferences() {
  // Logic to check if all images have a valid license reference in the database.
}

// --- Start the Import Process ---
importCSV(); 
