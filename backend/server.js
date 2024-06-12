const express = require('express');
const axios = require('axios');
const mongoose = require('mongoose');
const cors = require('cors');
const rateLimit = require('axios-rate-limit');

const app = express();
const port = process.env.PORT || 3001;
const databaseUri = process.env.MONGODB_URI;

// Rate limiting (adjust as needed)
const api = rateLimit(axios.create(), { maxRequests: 1, perMilliseconds: 6000 });

// Middleware
app.use(express.json());
app.use(cors());

// MongoDB Connection
mongoose.connect(databaseUri, {   })
  .then(() => console.log('Connected to MongoDB'))
  .catch(error => console.error('MongoDB connection error:', error));

// Define your Mushroom schema 
const MushroomSchema = new mongoose.Schema({
  scientificName: { type: String, required: true, unique: true }, // Add unique index
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
    });

    const newMushrooms = response.data.results.map(observation => {
      // Log observation here
      // log(observation); 

      let family = 'N/A'; 
      let genus = 'N/A';

      if (observation.consensus.ancestor_rank_names) {
        family = observation.consensus.ancestor_rank_names['family'] || 'N/A';
        genus = observation.consensus.ancestor_rank_names['genus'] || 'N/A';
      }

      return {
        scientificName: observation.consensus.name || 'N/A',
        latitude: observation.latitude || 0, 
        longitude: observation.longitude || 0, 
        imageUrl: observation.primary_image?.medium_url || 'placeholder.jpg', 
        description: observation.description || '',
        commonName: observation.consensus.matched_name || 'N/A',
        family,
        genus,
        // ... map other fields as needed, using the correct paths from the api2 response
      };
    });

    // Use insertMany for efficiency
    await Mushroom.insertMany(newMushrooms, { ordered: false, upsert: true });

    console.log(`Processed ${newMushrooms.length} mushrooms for page ${page}`);
    // Handle pagination
    if (response.data.more) {
      await fetchAndStoreMushrooms(page + 1); 
    }
  } catch (error) {
    console.error('Error fetching or storing mushroom data:', error);
    // Additional error handling logic (e.g., retry with exponential backoff)
  }
}

// Logging function
function log(message) {
  if (typeof console !== 'undefined' && console.log) {
    console.log(message); 
  } else {
    // You can handle logging differently, like writing to a file:
    // const fs = require('fs');
    // fs.writeFileSync('logs.txt', message + '\n', { flag: 'a' }); 
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
