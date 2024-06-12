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

// ... (other requires)

const app = express();
const port = process.env.PORT || 3001;
const databaseUri = process.env.MONGODB_URI

// Rate limiting (adjust as needed)
const api = rateLimit(axios.create(), { maxRequests: 1, perMilliseconds: 6000 });

// Middleware
app.use(express.json());
app.use(cors());

// MongoDB Connection
mongoose.connect(databaseUri, {  })
  .then(() => {
    console.log('Connected to MongoDB');

    // *** Initial Data Fetch Example *** 

    // Function to fetch mushroom data
    async function fetchMushroomData(scientificName) {
      try {
        // 1. Fetch Name Data
        const nameResponse = await axios.get(
          `https://mushroomobserver.org/api2/names?name=${scientificName}`
        );
        const nameData = nameResponse.data[0]; // Assuming the API returns an array of names

        // 2. Fetch Observation Data (for images and details)
        const observationResponse = await axios.get(
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
          gallery: observationData.images
            ? observationData.images.map((image) => ({
                url: image.url,
                thumbnailUrl: image.thumbnail_url || null, // Use null if thumbnail is missing
              }))
            : [], // Return an empty array if no images are found
          kingdom: nameData.kingdom,
          phylum: nameData.phylum,
          class: nameData.class,
          order: nameData.order,
          habitat: nameData.habitat,
          edibility: nameData.edibility, // Assuming the API provides edibility information
          distribution: nameData.distribution,
          wikipediaUrl: nameData.wikipedia_url,
          mushroomObserverUrl: `https://mushroomobserver.org/name/${nameData.id}`,
        };

        return mushroomData;
      } catch (error) {
        console.error(`Error fetching data for ${scientificName}:`, error);
        throw error;
      }
    }

    // Example Usage:
    fetchMushroomData("Amanita muscaria")
      .then((mushroomData) => {
        // Create a new Mushroom document with the fetched data
        const mushroom = new Mushroom(mushroomData);
        // Save the document to MongoDB
        return mushroom.save();
      })
      .then((savedMushroom) => {
        console.log("Mushroom data saved successfully:", savedMushroom);
      })
      .catch((error) => {
        console.error("Error:", error);
      });
  })
  .catch((error) => {
    console.error('MongoDB connection error:', error); 
  });


// Register routes
app.use('/api/mushrooms', mushroomsRouter);
app.use('/users', userRouter); 
app.use('/api/blog', blogRouter); 

// Start the Server 
app.listen(port, () => {
  console.log(`Server is running on port: ${port}`);
});
