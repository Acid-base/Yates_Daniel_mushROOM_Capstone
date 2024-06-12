const express = require('express');
const axios = require('axios');
const mongoose = require('mongoose');
const cors = require('cors');
const rateLimit = require('axios-rate-limit');

const app = express();
const port = process.env.PORT || 3001;
const databaseUri = process.env.MONGODB_URI

// Rate limiting (adjust as needed)
const api = rateLimit(axios.create(), { maxRequests: 1, perMilliseconds: 6000 });

// Middleware
app.use(express.json());
app.use(cors());

// MongoDB Connection
mongoose.connect(databaseUri, { useNewUrlParser: true, useUnifiedTopology: true  })
  .then(() => console.log('Connected to MongoDB'))
  .catch(error => console.error('MongoDB connection error:', error));

// Define your Mushroom schema 
const MushroomSchema = new mongoose.Schema({
  scientificName: { type: String, required: true },
  latitude: { type: Number, required: true }, 
  longitude: { type: Number, required: true },
  imageUrl: String,
  description: String,
  commonName: String,
  family: String,
  genus: String
  // ... add other relevant fields
});

const Mushroom = mongoose.model('Mushroom', MushroomSchema);

// --- Function to fetch and store mushroom data ---
async function fetchAndStoreMushrooms(page = 1) {
  try {
    const response = await api.get('https://mushroomobserver.org/api2/observations', { // Use api2
      params: {
        format: 'json',
        detail: 'high', // Important for nested data 
        page: page,
      },
      headers: {
        // You likely don't need an API key for GET requests in api2, but double-check the documentation
        // 'Authorization': `Bearer ${mushroomObserverApiKey}`, 
      },
    });

    const newMushrooms = response.data.results.map(observation => ({
      scientificName: observation.consensus.name || 'N/A',
      latitude: observation.latitude || 0, 
      longitude: observation.longitude || 0, 
      imageUrl: observation.primary_image?.medium_url || 'placeholder.jpg', 
      description: observation.description || '',
      commonName: observation.consensus.matched_name || 'N/A',
      family: observation.consensus.ancestor_rank_names['family'] || 'N/A',
      genus: observation.consensus.ancestor_rank_names['genus'] || 'N/A'
      // ... map other fields as needed, using the correct paths from the api2 response
    }));

    // Use bulkWrite with upsert: true to avoid duplicates
    const insertResult = await Mushroom.bulkWrite(newMushrooms.map(mushroom => ({
      updateOne: {
        filter: { scientificName: mushroom.scientificName, latitude: mushroom.latitude, longitude: mushroom.longitude }, 
        update: { $set: mushroom }, 
        upsert: true
      }
    })));

    console.log(`Processed ${newMushrooms.length} mushrooms (Inserted: ${insertResult.upsertedCount}, Updated: ${insertResult.modifiedCount}) for page ${page}`);

    // Handle pagination
    if (response.data.more) {
      await fetchAndStoreMushrooms(page + 1); 
    }
  } catch (error) {
    console.error('Error fetching or storing mushroom data:', error);
    // ... Additional error handling 
  }
}

// Example usage: Fetch data when the server starts
fetchAndStoreMushrooms(1)
  .then(() => console.log("Initial data fetch complete!"))
  .catch(err => console.error("Error during initial data fetch:", err));

// ... your API routes for /api/mushrooms (using the Mushroom model)

// Start the Server
app.listen(port, () => {
  console.log(`Server is running on port: ${port}`);
});

