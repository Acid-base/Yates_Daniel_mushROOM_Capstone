// controllers/mushroomController.js
const Mushroom = require('../models/MushroomModel');
const Favorite = require('../models/FavoriteModel'); // Assuming you created a Favorite model

// Get Mushrooms
const getMushrooms = async (req, res) => {
  // ... (existing getMushrooms logic from MushroomRoutes.js)
};

// Toggle Favorite
const toggleFavorite = async (req, res) => {
  const { mushroomId } = req.params;
  const userId = req.userId;

  try {
    // Check if mushroom exists
    const mushroom = await Mushroom.findById(mushroomId);
    if (!mushroom) {
      return res.status(404).json({ error: 'Mushroom not found' });
    }

    // Find existing favorite relationship
    let favorite = await Favorite.findOne({ userId, mushroomId }); 

    if (favorite) {
      // Remove from favorites
      await favorite.deleteOne();
      return res.json({ message: 'Removed from favorites' });
    } else {
      // Add to favorites
      favorite = new Favorite({ userId, mushroomId });
      await favorite.save();
      return res.json({ message: 'Added to favorites' });
    }
  } catch (error) {
    console.error('Error toggling favorite:', error);
    res.status(500).json({ error: 'Failed to toggle favorite' });
  }
};

module.exports = {
  getMushrooms,
  toggleFavorite,
};
