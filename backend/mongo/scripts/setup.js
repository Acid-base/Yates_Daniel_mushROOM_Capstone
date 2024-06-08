// backend/scripts/setup.js
const mongoose = require('mongoose');
const models = require('../models/index'); 

// Check if the connection is already established
// Database Connection 
(async () => { 
    try {
if (!mongoose.connection.readyState) { 
    // If the connection is not established, connect to the database
    mongoose.connect('mongodb://localhost:27017/mushroom', { 
            bufferTimeoutMS: 30000 // Increase the timeout to 30 seconds 
        });
    console.log('Connected to MongoDB'); 
} else {
    console.log('MongoDB connection already established');
}

        // --- Index Creation and Optimization ---
        await createIndexIfDoesNotExist(models.Observation, { name: 1, when: 1 }, 'name_1_when_1');

        // Custom index creation for location_1_when_1 index
        const observationsCollection = models.Observation.collection;
        observationsCollection.indexExists('location_1_when_1', (err, exists) => {
          if (err) {
            console.error('Error checking if index exists:', err);
          } else if (exists) {
            // Check if the index is correct
            observationsCollection.indexInformation({ location: 1, when: 1 }, (err, info) => {
              if (err) {
                console.error('Error getting index information:', err);
              } else if (!info.unique) {
                // The index is not unique, so drop it and recreate it
                observationsCollection.dropIndex('location_1_when_1', (err) => {
                  if (err) {
                    console.error('Error dropping index:', err);
                  } else {
                    // Recreate the index with the unique option
                    observationsCollection.createIndex({ location: 1, when: 1 }, { unique: true }, (err) => {
                      if (err) {
                        console.error('Error creating index:', err);
                      } else {
                        console.log('Index created successfully.');
                      }
                    });
                  }
                });
              }
            });
          } else {
            // The index does not exist, so create it
            observationsCollection.createIndex({ location: 1, when: 1 }, { unique: true }, (err) => {
              if (err) {
                console.error('Error creating index:', err);
              } else {
                console.log('Index created successfully.');
              }
            });
          }
        });

        await createIndexIfDoesNotExist(models.Location, { name: 1 }, 'location_name_1');
        await createIndexIfDoesNotExist(models.NameDescription, { name: 1 }, 'nameDescription_name_1');
        await createIndexIfDoesNotExist(models.NameClassification, { name: 1 }, 'nameClassification_name_1'); 
        //  ... (Add similar index creation for other models)

    } catch (error) {
        console.error("Error connecting to MongoDB or creating indexes:", error); 
        process.exit(1); 
    } 
})();

// Helper function to create an index if it doesn't exist
async function createIndexIfDoesNotExist(model, indexFields, indexName) {
    try {
        const indexExists = await model.collection.indexExists(indexName);
        if (!indexExists) {
            await model.collection.createIndex(indexFields, { name: indexName });
            console.log(`Created index "${indexName}" on ${model.modelName} collection`);
        } else {
            console.log(`Index "${indexName}" already exists on ${model.modelName} collection`);
        }
    } catch (error) {
        console.error(`Error creating index "${indexName}":`, error);
    }
}