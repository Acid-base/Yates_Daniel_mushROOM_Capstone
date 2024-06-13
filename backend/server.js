// server.js
const express = require('express');
const mongoose = require('mongoose');
const axios = require('axios');
const rateLimit = require('axios-rate-limit');
const { APIError, DatabaseError } = require('./middleware/customErrors');
const Mushroom = require('./models/MushroomModel');
const User = require('./models/UserModel');
const BlogPost = require('./models/BlogPostModel');

const logger = require('./middleware/logger');
const authenticateToken = require('./middleware/auth');
const userRoutes = require('./routes/UserRoutes');
const mushroomRouter = require('./routes/MushroomRoutes'); 
const cacheManager = require('./data/cacheManager.js');
const blogRouter = require('./routes/BlogRoutes');
const blogController = require('./controllers/blogController');
const db = require('./data/db'); 
const mushroomService = require('./data/db'); // Import from db.js
// Removed the fetchDataFromAPI and fetchAndStoreMushroomData functions from here 
// require('dotenv').config();

const cors = require('cors');
const { body, validationResult } = require('express-validator'); 

const app = express();
const port = 3001;
// Removed the fetchDataFromAPI and fetchAndStoreMushroomData functions from here 
app.listen(port, async () => {
  try {
    await db.connectToDatabase();
    console.log(`Mushroom Explorer backend listening at http://localhost:${port}`);

    // Call fetchAndStoreMushroomData 
    await mushroomService.fetchAndStoreMushroomData(); 
const port = process.env.PORT || 3001;
const databaseUri = process.env.MONGODB_URI;

const apiLimiter = rateLimit({
  windowMs: 60 * 1000, // 1 minute
  max: 10, // Limit each IP to 10 requests per windowMs
  message: 'Too many requests, please try again later.'
});

app.use('/api', apiLimiter);
app.use(cors());
app.use(express.json());

mongoose.connect(databaseUri, { useNewUrlParser: true, useUnifiedTopology: true })
  .then(() => {
    console.log('Connected to MongoDB');
    // Start fetching mushrooms data once MongoDB connection is established
    fetchAllMushrooms();
  })
  .catch((error) => {
    console.error('Error connecting to MongoDB:', error.message);
  });

const api = axios.create();

async function fetchMushroomData(observationId) {
  try {
    const observationResponse = await api.get(
      `https://mushroomobserver.org/api2/observations/${observationId}?detail=high&format=json`
    );
    const observation = observationResponse.data.results[0];

    if (!observation || !observation.name_id) {
      console.warn(`Skipping observation ID: ${observationId} due to missing or invalid data.`);
      return null; // Return null to indicate invalid data
    }

    const nameId = observation.name_id;
    const nameResponse = await api.get(
      `https://mushroomobserver.org/api2/names?id=${nameId}&detail=high&format=json`
    );
    const nameDetails = nameResponse.data.results[0];

    const mushroomData = {
      scientificName: nameDetails.text_name,
      latitude: observation.latitude || null,
      longitude: observation.longitude || null,
      imageUrl:
        observation.primary_image
          ? `https://mushroomobserver.org/images/${observation.primary_image}`
          : null,
      description: nameDetails.description,
      commonName: nameDetails.common_name,
      family: nameDetails.family,
      genus: nameDetails.genus,
      region: observation.location_name || null,
      gallery: observation.images
        ? observation.images.map((image) => ({
            url: `https://mushroomobserver.org/images/${image}`,
            thumbnailUrl: `https://mushroomobserver.org/images/thumbnails/${image}` || null,
          }))
        : [],
      kingdom: nameDetails.kingdom,
      phylum: nameDetails.phylum,
      class: nameDetails.class,
      order: nameDetails.order,
      habitat: nameDetails.habitat,
      edibility: nameDetails.edibility,
      distribution: nameDetails.distribution,
      wikipediaUrl: nameDetails.wikipedia_url,
      mushroomObserverUrl: `https://mushroomobserver.org/name/${nameDetails.id}`,
    };

    return mushroomData;
  } catch (error) {
    console.error('Error starting the server:', error); 
  }
    console.error("Error fetching mushroom data:", error.message);
    throw error;
  }
}

async function fetchAndSaveMushroom(observationId) {
  try {
    const mushroomData = await fetchMushroomData(observationId);
    if (!mushroomData) {
      // Skip if mushroomData is null due to invalid data
      return null;
    }

    const existingMushroom = await Mushroom.findOne({
      scientificName: mushroomData.scientificName,
      mushroomObserverUrl: mushroomData.mushroomObserverUrl,
    });

    if (!existingMushroom) {
      const newMushroom = new Mushroom(mushroomData);
      await newMushroom.save();
      return newMushroom;
    } else {
      return existingMushroom;
    }
  } catch (error) {
    console.error(`Error fetching and saving mushroom with observation ID: ${observationId}`, error.message);
    throw error;
  }
}

async function fetchAllMushrooms() {
  let pageNumber = 1;
  let totalPages = 1;

  while (pageNumber <= totalPages) {
    try {
      const response = await api.get(
        `https://mushroomobserver.org/api2/observations?name=Agaricus&detail=low&format=json&page=${pageNumber}`
      );

      const { results, number_of_pages } = response.data;
      totalPages = number_of_pages;

      for (const observation of results) {
        const observationId = observation.id;
        let retryCount = 0;
        let mushroomData = null;

        // Retry mechanism with exponential backoff for rate limits
        while (retryCount < 3) {
          try {
            mushroomData = await fetchAndSaveMushroom(observationId);
            break; // Break loop if successful
          } catch (error) {
            if (error.response && error.response.status === 429) {
              // Rate limit exceeded, implement backoff
              const backoffDelay = Math.pow(2, retryCount) * 1000; // Exponential backoff
              console.warn(`Rate limit exceeded. Retrying in ${backoffDelay / 1000} seconds.`);
              await new Promise((resolve) => setTimeout(resolve, backoffDelay));
            } else {
              // Other errors, log and skip observation
              console.error(`Error fetching and saving mushroom with observation ID: ${observationId}`, error.message);
              break; // Exit retry loop on non-rate-limit errors
            }
          }
          retryCount++;
        }

        if (!mushroomData) {
          console.warn(`Skipping observation ID: ${observationId} after ${retryCount} attempts.`);
        }
      }

      pageNumber += 1;
    } catch (error) {
      console.error("Error fetching observations:", error.message);
      break;
    }
  }
}

// Express routes
app.get('/', (req, res) => {
  res.send('Welcome to the Mushroom Observer API integration!');
});

// Start the server
app.listen(port, () => {
  console.log(`Server is running on port ${port}`);
});
