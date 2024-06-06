// routes/mushrooms.js - Defines the API endpoints for managing mushrooms

const express = require('express');
const router = express.Router();
const Mushroom = require('../models/Mushroom'); // Import the Mushroom model
console.log(__dirname)
// GET /mushrooms - Get a list of mushrooms
router.get('/', async (req, res) => {
  const searchTerm = req.query.q; // Get the search term from the query parameter (e.g., /mushrooms?q=chanterelle)

  try { 
    let mushrooms; // Variable to store the result of the MongoDB query

    if (searchTerm) { 
      // If a search term is provided, query the database 
      mushrooms = await Mushroom.find({
        $or: [
          // Search in either commonName or scientificName
          { commonName: { $regex: searchTerm, $options: 'i' } }, // Use a case-insensitive regex search
          { scientificName: { $regex: searchTerm, $options: 'i' } }
        ]
      });
    } else {
      // If no search term, get all mushrooms from the database
      mushrooms = await Mushroom.find();
    }

    // Send the found mushrooms as a JSON response to the client
    res.json(mushrooms); 

  } catch (error) {
    console.error("Error fetching data:", error);
    // Send a 500 (Internal Server Error) response if something goes wrong
    res.status(500).json({ error: 'Error fetching data' }); 
  }
});

// Export the router so it can be used in other parts of your backend application
module.exports = router; 
