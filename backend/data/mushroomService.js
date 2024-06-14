const axios = require('axios');
const rateLimit = require('axios-rate-limit'); // Assuming you're using 'axios-rate-limit'
const express = require('express');
const mongoose = require('mongoose');
const { APIError, DatabaseError } = require('../../middleware/customErrors.js');
const Mushroom = require('../../models/MushroomModel.js');
const User = require('../../models/UserModel.js');
const BlogPost = require('../../models/BlogPostModel.js');

const logger = require('../../middleware/logger.js');
const authenticateToken = require('../../middleware/auth.js');
const userRoutes = require('../routes/UserRoutes');
const mushroomRouter = require('../routes/MushroomRoutes');
const blogRouter = require('../routes/BlogRoutes');
const blogController = require('../controllers/blogController');
const db = require('./db');

require('dotenv').config();

const cors = require('cors');
const { body, validationResult } = require('express-validator');

const app = express();
const port = 3008;

// Middleware
app.use(express.json()); // Parse JSON request bodies
app.use(cors()); // Enable CORS for cross-origin requests

// Rate Limiting (using axios-rate-limit)
const api = rateLimit(axios.create(), { maxRequests: 1, perMilliseconds: 6000 });

// Authentication middleware
app.use(authenticateToken);

// Routes
app.use('/users', userRoutes);
app.use('/mushrooms', mushroomRouter);
app.use('/blogs', blogRouter);

// Function to fetch and store mushroom data
async function fetchAndStoreMushroomData(observationId) {
  const observationUrl = `https://mushroomobserver.org/api2/observations?id=${observationId}&detail=high&format=json`;

  try {
    const response = await fetch(observationUrl);
    const data = await response.json();

    const observation = data.results[0];
    const mushroomData = {
      scientificName: observation.consensus_name,
      latitude: observation.location.gps.latitude,
      longitude: observation.location.gps.longitude,
      imageUrl: observation.primary_image_url, // assuming this is included in high detail
      description: observation.notes, // or observation.details
      commonName: observation.name_common, // if available
      family: observation.name_family,
      genus: observation.name_genus,
      region: observation.location.region,
      kingdom: observation.name_kingdom,
      phylum: observation.name_phylum,
      class: observation.name_class,
      order: observation.name_order,
      habitat: observation.habitat, // if available
      edibility: observation.edibility, // if available
      distribution: observation.distribution, // if available
      mushroomObserverUrl: `https://mushroomobserver.org/observations/${observation.id}`,
      // other fields from observation data
    };

    // Save or update the mushroom document in MongoDB
    const updatedMushroom = await Mushroom.findOneAndUpdate(
      { scientificName: mushroomData.scientificName }, // query condition
      mushroomData, // update data
      { upsert: true, new: true } // options
    );

    console.log('Mushroom data saved or updated successfully:', updatedMushroom);
  } catch (error) {
    console.error('Error fetching or saving mushroom data:', error);
  }
}

// Start the server
app.listen(port, async () => {
  try {
    await db.connectToDatabase();
    console.log(`Mushroom Explorer backend listening at http://localhost:${port}`);

    // Example: Fetch and store data for observation ID 12345
    await fetchAndStoreMushroomData(12345); 
  } catch (error) {
    console.error('Error starting the server:', error);
  }
});
