// backend/services/mushroomService.js
const axios = require('axios');
const Mushroom = require('../models/MushroomModel');
const { getRegionFromCoordinates } = require('../helpers'); 

// ... (Your MongoDB connection setup)

async function fetchAndStoreMushroomData(scientificName) {
  try {
    // Fetch data from the API
    const response = await axios.get(
      `https://mushroomobserver.org/api2/names?name=${scientificName}`
    );

    // Check for API errors (e.g., status codes 400, 404, 500)
    if (!response.ok) {
      throw new Error(
        `API request failed with status ${response.status}: ${response.statusText}`
      );
    }

    // Process the data
    const data = response.data[0]; // Assuming the API returns an array of names

    // Combine data from different endpoints (if needed)
    // ...

    // Check for data consistency (ensure uniqueness)
    const existingMushroom = await Mushroom.findOne({ scientificName });
    if (existingMushroom) {
      console.log(
        `Mushroom with scientific name ${scientificName} already exists. Skipping.`
      );
      return; // Skip saving if it already exists
    }
    // Create a new Mushroom document
    const mushroom = new Mushroom(data); // Or use combined data

    // Save the document to MongoDB
    await mushroom.save();
    console.log(`Mushroom data saved for ${scientificName}`);
  } catch (error) {
    console.error(`Error fetching data for ${scientificName}:`, error);
  }
}

  // ... (Your MongoDB connection setup)

  // Example scientific name
  const scientificName = 'Amanita muscaria';

  // Make the initial request
fetchAndStoreMushroomData(scientificName);

  // Set up a timer to make requests every 10 seconds
  setInterval(async () => {
    await fetchAndStoreMushroomData(scientificName);
  }, 10000);

export default fetchAndStoreMushroomData;
