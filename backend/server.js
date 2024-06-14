// server.js
const rateLimit = require('axios-rate-limit');
const axios = require('axios');
const express = require('express');
const cors = require('cors');
const { body, validationResult } = require('express-validator');
require('dotenv').config();

const db = require('./db'); // Import database module
const userRoutes = require('./routes/UserRoutes');
const mushroomRouter = require('./routes/MushroomRoutes');
const blogRouter = require('./routes/BlogRoutes');
const blogController = require('./controllers/blogController');
const authenticateToken = require('./middleware/auth');
const logger = require('./middleware/logger');

const app = express();
const port = process.env.PORT || 3001;

// Rate limiting (adjust as needed)
const api = rateLimit(axios.create(), { maxRequests: 1, perMilliseconds: 6000 });

// Apply retry logic to axios instance
retry(api, {
  retries: 3, // Number of retries
  retryDelay: (retryCount) => {
    console.log(`Retry attempt: ${retryCount}`);
    return retryCount * 2000; // Time between retries in milliseconds
  },
  retryCondition: (error) => {
    // Retry on 429 status code
    return error.response.status === 429;
  },
});

// Middleware
app.use(express.json()); // Parse JSON request bodies
app.use(cors()); // Enable CORS for cross-origin requests

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
    const response = await api.get(observationUrl);
    const data = response.data;

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

    logger.info('Mushroom data saved or updated successfully:', updatedMushroom);
  } catch (error) {
    logger.error('Error fetching or saving mushroom data:', error);
  }
}

// Start the server
app.listen(port, async () => {
  try {
    await db.connectToDatabase(); // Connect to the database
    logger.info(`Mushroom Explorer backend listening at http://localhost:${port}`);

    // Seed the database with initial data
    await db.seedDatabase(); 

    // Example: Fetch and store data for observation ID 12345
    // await fetchAndStoreMushroomData(12345); 
  } catch (error) {
    logger.error('Error starting the server:', error);
  }
});

// Error Handling
app.use((err, req, res, next) => {
  logger.error(err.stack); // Log the error to the error file
  res.status(500).json({ error: 'Something went wrong!' });
});
