// backend/services/mushroomService.js
const axios = require('axios');
const Mushroom = require('../models/MushroomModel');
const { getRegionFromCoordinates } = require('../helpers'); 

// Function to fetch and store mushroom data
async function fetchAndStoreMushrooms(page = 1) {
  // ... (Your existing logic to fetch and store mushroom data)
}

module.exports = { fetchAndStoreMushrooms }; 
