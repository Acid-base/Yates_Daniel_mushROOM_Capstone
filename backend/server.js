const express = require('express');
const axios = require('axios');
const mongoose = require('mongoose');
const cors = require('cors');
const rateLimit = require('axios-rate-limit');
require('dotenv').config(); // Load environment variables at the top
const Mushroom = require('./models/Mushroom'); // Import the Mushroom model

const app = express();
const port = process.env.PORT || 3001;
const databaseUri = process.env.MONGODB_URI;

// Rate limiting (adjust as needed)
const api = rateLimit(axios.create(), { maxRequests: 1, perMilliseconds: 6000 });

// Middleware
app.use(express.json());
app.use(cors());

// MongoDB Connection
mongoose.connect(databaseUri, { useNewUrlParser: true, useUnifiedTopology: true })
  .then(() => {
    console.log('Connected to MongoDB');
    // Start your server or perform other actions
  })
  .catch((error) => {
    console.error('MongoDB connection error:', error); 
    // Handle the error appropriately
  });

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

      // Determine the region based on latitude and longitude
      let region = getRegionFromCoordinates(observation.latitude, observation.longitude); 
      return {
        scientificName: observation.consensus.name || 'N/A',
        latitude: observation.latitude || 0, 
        longitude: observation.longitude || 0, 
        imageUrl: observation.primary_image?.medium_url || 'placeholder.jpg', 
        description: observation.description || '',
        commonName: observation.consensus.matched_name || 'N/A',
        family,
        genus,
        region, // Added region field
        // ... map other fields as needed, using the correct paths from the api2 response
      };
    });

    // Use bulkWrite with upsert: true to avoid duplicates
    const insertResult = await Mushroom.bulkWrite(newMushrooms.map(mushroom => ({
      updateOne: {
        filter: { scientificName: mushroom.scientificName, latitude: mushroom.latitude, longitude: mushroom.longitude },
        update: { $set: mushroom },
        upsert: true
      }
    })));
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

// Helper function to get the region from coordinates (you'll need to implement this)
function getRegionFromCoordinates(latitude, longitude) {
  // ... Use geocoding service or a region lookup database to determine the region.
  // Example (using a lookup table, you'll need to create a regions database or use a pre-built library):
  // const regions = require('./regions.json'); // Replace with your regions lookup data
  // return regions.find(region => latitude >= region.latMin && latitude <= region.latMax && longitude >= region.lonMin && longitude <= region.lonMax)?.name || 'Unknown'; 
  // You can also use an external API like Google Maps API or a geocoding library
  return 'Unknown'; // Placeholder - replace with your actual region determination logic
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

// Register the user routes
app.use('/users', require('./routes/users'));
// Start the Server
app.listen(port, () => {
  console.log(`Server is running on port: ${port}`);
});
