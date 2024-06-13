const rateLimit = require('axios-rate-limit');
const axios = require('axios');
const express = require('express');
const mongoose = require('mongoose');
require('dotenv').config();

const cors = require('cors');
const { body, validationResult } = require('express-validator');

const Mushroom = require('./models/MushroomModel');
const mushroomsRouter = require('./routes/MushroomRoutes');
const userRouter = require('./routes/UserRoutes');
const blogRouter = require('./routes/BlogRoutes');
const app = express();
const port = process.env.PORT || 3001;
const databaseUri = process.env.MONGODB_URI;

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
app.use(express.json());
app.use(cors());

// MongoDB Connection
mongoose.connect(databaseUri, {  })
  .then(() => {
    console.log('Connected to MongoDB');
    app.listen(port, () => {
      console.log(`Server is running on port ${port}`);
    });
  })
  .catch((error) => {
    console.error('Error connecting to MongoDB:', error.message);
  });

// Function to fetch mushroom data
async function fetchMushroomData(scientificName) {
  try {
    // 1. Fetch Name Data
    const nameResponse = await api.get(
      `https://mushroomobserver.org/api2/names?name=${scientificName}`
    );
    const nameData = nameResponse.data[0]; // Assuming the API returns an array of names

    // 2. Fetch Observation Data (for images and details)
    const observationResponse = await api.get(
      `https://mushroomobserver.org/api2/observations?name=${scientificName}`
    );
    const observationData = observationResponse.data;

    // 3. Combine Data from Different Endpoints
    const mushroomData = {
      scientificName: nameData.text_name,
      latitude: nameData.latitude || null, // Use null if latitude is missing
      longitude: nameData.longitude || null, // Use null if longitude is missing
      imageUrl:
        observationData.images && observationData.images.length > 0
          ? observationData.images[0].url
          : null, // Handle cases where no images are available
      description: nameData.description,
      commonName: nameData.common_name,
      family: nameData.family,
      genus: nameData.genus,
      region: nameData.region || null, // Use null if region is missing
    };

    return mushroomData;
  } catch (error) {
    console.error("Error fetching mushroom data:", error.message);
    throw error;
  }
}

async function fetchAndSaveMushroom(scientificName) {
  try {
    const mushroomData = await fetchMushroomData(scientificName);
    if (!mushroomData) {
      return null;
    }

    const existingMushroom = await Mushroom.findOne({
      scientificName: mushroomData.scientificName,
    });

    if (!existingMushroom) {
      const newMushroom = new Mushroom(mushroomData);
      await newMushroom.save();
      return newMushroom;
    } else {
      return existingMushroom;
    }
  } catch (error) {
    console.error(`Error fetching and saving mushroom with scientific name: ${scientificName}`, error.message);
    throw error;
  }
}

async function seedDatabase() {
  try {
    const scientificNames = ['Amanita muscaria', 'Boletus edulis', 'Cantharellus cibarius', 'Cortinarius caperatus', 'Lactarius deliciosus'];
    
    for (let scientificName of scientificNames) {
      await fetchAndSaveMushroom(scientificName);
    }

    console.log(success);
  } catch (error) {
    console.error('Error seeding database:', error.message);
  }
}

seedDatabase();

// Routes
app.use('/mushrooms', mushroomsRouter);
app.use('/users', userRouter);
app.use('/blogs', blogRouter);

// Error Handling
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).send('Something went wrong!');
});