const Mushroom = require('../models/Mushroom');

exports.getMushrooms = async (req, res) => {
  const mushrooms = await Mushroom.find();
  res.send(mushrooms);
};

// Add other controller functions for creating, updating, deleting mushrooms
