const User = require('../models/User');

exports.getUsers = async (req, res) => {
  const users = await User.find();
  res.send(users);
};

// Add other controller functions for creating, updating, deleting users
