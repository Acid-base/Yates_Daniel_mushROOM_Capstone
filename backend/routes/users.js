const express = require('express');
const router = express.Router();
const authenticateToken = require('../middleware/auth'); // Import middleware

const userController = require('../controllers/userController');
const Mushroom = require('../models/Mushroom'); // Assuming you have a Mushroom model
const User = require('../models/User'); // Assuming you have a User model

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

// New route for fetching user details
router.get('/me', authenticateToken, async (req, res) => {
  try {
    const user = await User.findById(req.userId)
      .select('-password') // Exclude password from response
      .populate('favorites', '-userId') // Populate favorites for the user
      .populate('savedMushrooms', '-userId'); // Populate saved mushrooms for the user (if applicable)

    res.json(user);
  } catch (error) {
    console.error('Error fetching user:', error);
    res.status(500).json({ error: 'Failed to fetch user' });
  }
});

router.post('/register', userController.registerUser); // Register route
router.post('/login', userController.loginUser); // Login route

// Add other routes for creating, updating, deleting users
router.put('/:userId/update', authenticateToken, async (req, res) => {
  try {
    // Validate the request body (add validation for required fields)
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

    const userId = req.params.userId;
    if (userId !== req.userId) {
      return res.status(401).json({ error: 'Unauthorized to update this profile' });
    }

    // Update the user's profile information
    const updatedUser = await User.findByIdAndUpdate(userId, req.body, { new: true })
      .select('-password'); // Exclude password from response

    res.json(updatedUser);
  } catch (error) {
    console.error('Error updating user:', error);
    res.status(500).json({ error: 'Failed to update user' });
  }
});
router.post('/favorites/:mushroomId', authenticateToken, userController.toggleFavorite); 

module.exports = router;
