// UserModel.js
const mongoose = require('mongoose');

const userSchema = new mongoose.Schema({
  name: {
    type: String,
    required: true,
  },
  email: {
    type: String,
    required: true,
    unique: true,
  },
  password: {
    type: String,
    required: true,
  },
  profile: {
    location: String, // Optional: user's location
    avatarUrl: String, // Optional: URL of user's avatar
    bio: String, // Optional: brief user bio
  }
});

module.exports = mongoose.model('User', userSchema);
