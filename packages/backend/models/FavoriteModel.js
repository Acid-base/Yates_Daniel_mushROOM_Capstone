// models/FavoriteModel.js
const mongoose = require('mongoose');

const favoriteSchema = new mongoose.Schema({
  userId: { 
    type: mongoose.Schema.Types.ObjectId, 
    ref: 'User', 
    required: true 
  },
  mushroomId: { 
    type: mongoose.Schema.Types.ObjectId, 
    ref: 'Mushroom', 
    required: true 
  },
  favoritedAt: {
    type: Date,
    default: Date.now
  }
});

module.exports = mongoose.model('Favorite', favoriteSchema); 
