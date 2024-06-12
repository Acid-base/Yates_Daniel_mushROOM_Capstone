const express = require('express');
const router = express.Router();
const authenticateToken = require('../middleware/auth'); // Import middleware

const userController = require('../controllers/userController');
const Mushroom = require('../models/Mushroom'); // Assuming you have a Mushroom model

// Protected route (requires authentication)
router.get('/', authenticateToken, async (req, res) => {
  const searchTerm = req.query.q || '';
  const page = parseInt(req.query.page) || 1;
  const userId = req.userId; // Get the user ID from the authenticated request

  try {
    let query = {};

    if (searchTerm) {
      query = {
        $or: [
          { commonName: { $regex: searchTerm, $options: 'i' } },
          { scientificName: { $regex: searchTerm, $options: 'i' } }
        ]
      };
    }

    const pageSize = 20;
    const skip = (page - 1) * pageSize;

    let mushrooms;

    // If user is logged in, include favorites
    if (userId) {
      mushrooms = await Mushroom.find(query)
        .skip(skip)
        .limit(pageSize)
        .populate({
          path: 'favorites',
          match: { userId: userId }, // Only populate favorites for the current user
          select: 'favoritedAt' // Optional: Select only the favoritedAt field
        });
    } else {
      mushrooms = await Mushroom.find(query)
        .skip(skip)
        .limit(pageSize);
    }

    const totalMushrooms = await Mushroom.countDocuments(query);

    res.json({
      results: mushrooms,
      currentPage: page,
      totalPages: Math.ceil(totalMushrooms / pageSize),
    });

  } catch (error) {
    console.error("Error fetching data:", error);
    res.status(500).json({ error: 'Error fetching data' });
  }
});

router.post('/register', userController.registerUser); // Register route
router.post('/login', userController.loginUser); // Login route

// Add other routes for creating, updating, deleting users
router.post('/favorites/:mushroomId', authenticateToken, userController.toggleFavorite); 

module.exports = router;
