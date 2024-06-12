const express = require('express');
const axios = require('axios');
const mongoose = require('mongoose');
const cors = require('cors');
const rateLimit = require('axios-rate-limit');
require('dotenv').config(); 
const Mushroom = require('./models/Mushroom');
const { body, validationResult } = require('express-validator');

const app = express();
const port = process.env.PORT || 3001;
const databaseUri = process.env.MONGODB_URI;

// Rate limiting (adjust as needed)
const api = rateLimit(axios.create(), { maxRequests: 1, perMilliseconds: 6000 });

// Middleware
app.use(express.json());
app.use(cors());

// MongoDB Connection
mongoose.connect(databaseUri, {  })
  .then(() => {
    console.log('Connected to MongoDB');
  })
  .catch((error) => {
    console.error('MongoDB connection error:', error); 
  });

// --- Function to fetch and store mushroom data ---
async function fetchAndStoreMushrooms(page = 1) {
  try {
    const response = await api.get('https://mushroomobserver.org/api2/observations', {
      params: {
        format: 'json',
        detail: 'high', 
        page: page,
      },
    });

    const newMushrooms = response.data.results.map(observation => {
      let family = 'N/A'; 
      let genus = 'N/A';

      if (observation.consensus.ancestor_rank_names) {
        family = observation.consensus.ancestor_rank_names['family'] || 'N/A';
        genus = observation.consensus.ancestor_rank_names['genus'] || 'N/A';
      }

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
        region, 
      };
    });

    const insertResult = await Mushroom.bulkWrite(newMushrooms.map(mushroom => ({
      updateOne: {
        filter: { scientificName: mushroom.scientificName, latitude: mushroom.latitude, longitude: mushroom.longitude },
        update: { $set: mushroom },
        upsert: true
      }
    })));
    console.log(`Processed ${newMushrooms.length} mushrooms for page ${page}`);
    if (response.data.more) {
      await fetchAndStoreMushrooms(page + 1); 
    }
  } catch (error) {
    console.error('Error fetching or storing mushroom data:', error);
  }
}

// Helper function to get the region from coordinates
function getRegionFromCoordinates(latitude, longitude) {
  return 'Unknown';
}

// Example usage: Fetch data when the server starts
fetchAndStoreMushrooms(1)
  .then(() => console.log("Initial data fetch complete!"))
  .catch(err => console.error("Error during initial data fetch:", err));

// ... (Your other code)

// Register the user routes
app.use('/users', require('./routes/users'));

// Register the mushrooms route
const mushroomsRouter = express.Router();
mushroomsRouter.post('/mushrooms', 
  [
    body('scientificName').notEmpty().trim().escape(), 
    body('latitude').isFloat(),
    body('longitude').isFloat(),
    body('imageUrl').optional().isURL(), 
    // ... add validation for other fields
  ], 
  async (req, res) => {
    // Validate the request body
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

    try {
      const newMushroom = new Mushroom(req.body);
      await newMushroom.save();
      res.status(201).json(newMushroom);
    } catch (error) {
      console.error('Error creating mushroom:', error);
      if (error.code === 11000) {
        res.status(409).json({ error: 'A mushroom with this scientific name already exists' });
      } else {
        res.status(500).json({ error: 'Failed to create mushroom' });
      }
    }
  }
);
app.use('/api/mushrooms', mushroomsRouter); 

// Register the blog routes
app.use('/api/blog', require('./routes/blog'));
// Start the Server
app.listen(port, () => {
  console.log(`Server is running on port: ${port}`);
});
