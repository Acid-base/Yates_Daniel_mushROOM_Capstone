// routes/mushrooms.js 
const express = require('express');
const router = express.Router();
const Mushroom = require('../models/Mushroom');
const authenticateToken = require('../middleware/auth');

// GET /mushrooms - Get a list of mushrooms
// Protected route - requires authentication 
router.get('/', authenticateToken, async (req, res) => {
  const searchTerm = req.query.q; 

  try { 
    let mushrooms; 

    if (searchTerm) { 
      mushrooms = await Mushroom.find({
        $or: [
          { commonName: { $regex: searchTerm, $options: 'i' } },
          { scientificName: { $regex: searchTerm, $options: 'i' } }
        ]
      });
    } else {
      mushrooms = await Mushroom.find();
    }

    res.setHeader('Content-Type', 'application/json'); // Set Content-Type to JSON
    console.log(mushrooms);
    res.json(mushrooms); // Send the data as JSON

  } catch (error) {
    console.error("Error fetching data:", error);
  
    res.status(500).json({ error: 'Error fetching data' }); 
  }
});

module.exports = router;
