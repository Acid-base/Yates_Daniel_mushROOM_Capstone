const express = require('express');
const router = express.Router();
const mushroomController = require('../controllers/mushroomController'); 
const authenticateToken = require('../middleware/auth'); // Assuming you need authentication

// GET /mushrooms - Get a list of mushrooms
// Protected route - requires authentication
router.get('/', authenticateToken, async (req, res) => {
  const { page = 1, limit = 10, region, edibility } = req.query;
  const query = {};
  if (region) {
    query.region = region;
  }

  if (edibility) {
    query.edibility = edibility;
  }

  try {
    const mushrooms = await Mushroom.find(query)
      .skip((page - 1) * limit)
      .limit(parseInt(limit));

    const total = await Mushroom.countDocuments(query);

    res.json({
      mushrooms,
      total,
      page: parseInt(page),
      pages: Math.ceil(total / limit),
    });
  } catch (error) {
    console.error('Error fetching mushrooms:', error);
    res.status(500).json({ error: 'Error fetching mushrooms' });
  }
});

module.exports = router;

// Example mushroom routes 
router.get('/', authenticateToken, mushroomController.getMushrooms);
router.post('/:mushroomId/favorites', authenticateToken, mushroomController.toggleFavorite); 
module.exports = router;
