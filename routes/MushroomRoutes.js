// routes/MushroomRoutes.js
const express = require('express');
const router = express.Router(); 
const { body, validationResult } = require('express-validator');
const Mushroom = require('../models/MushroomModel'); 

router.post('/',
  [
    body('scientificName').notEmpty().trim().escape(),
    body('latitude').isFloat(),
    body('longitude').isFloat(),
    body('imageUrl').optional().isURL(),
    // ... add validation for other fields
  ],
  async (req, res) => {
    // ... (Your validation and mushroom creation logic from before)
  }
);

module.exports = router; 
const express = require('express');
const router = express.Router();
const authenticateToken = require('../middleware/auth');
const Mushroom = require('../models/MushroomModel');

// GET /mushrooms - Get a list of mushrooms
// Protected route - requires authentication
router.get('/', authenticateToken, async (req, res) => {
  const searchTerm = req.query.q; // Search term from query parameter
  const page = parseInt(req.query.page) || 1; // Page number, default to 1
  const pageSize = 10; // Number of items per page (adjust as needed)

  try {
    let query = {}; // Initial query object

    // Apply search term if provided
    if (searchTerm) {
      query = {
        $or: [
          { commonName: { $regex: searchTerm, $options: 'i' } },
          { scientificName: { $regex: searchTerm, $options: 'i' } }
        ]
      };
    }

    // Calculate skip value for pagination
    const skip = (page - 1) * pageSize;

    // Find mushrooms based on the query, skip, and limit
    const mushrooms = await Mushroom.find(query)
      .skip(skip)
      .limit(pageSize);

    // Get the total number of mushrooms for pagination
    const totalMushrooms = await Mushroom.countDocuments(query);

    // Send the paginated results
    res.json({
      results: mushrooms,
      currentPage: page,
      totalPages: Math.ceil(totalMushrooms / pageSize),
    });
  } catch (error) {
    console.error('Error fetching mushrooms:', error);
    res.status(500).json({ error: 'Error fetching mushrooms' });
  }
});

module.exports = router;
