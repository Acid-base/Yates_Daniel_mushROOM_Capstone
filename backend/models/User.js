// backend/models/User.js 
const mongoose = require('mongoose'); 

const userSchema = new mongoose.Schema({
  name: {
    type: String,
    required: true 
  },
  email: {
    type: String,
    required: true,
    unique: true 
  }
  // Add more user-related fields as needed 
});

module.exports = mongoose.model('User', userSchema);

