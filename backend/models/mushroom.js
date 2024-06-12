// models/mushroom.js 
const mongoose = require('mongoose');

const MushroomSchema = new mongoose.Schema({
  // Basic Information
  scientificName: { type: String, required: true, unique: true }, // Unique scientific name
  commonName: { type: String, required: true },
  // Location
  latitude: { type: Number, required: true },
  longitude: { type: Number, required: true },
  // Image Information
  imageUrl: { type: String, required: true }, // Primary image URL
  additionalImages: [String], // Array to store additional image URLs 
  // Description (can be more detailed if needed)
  description: String,
  // Taxonomy
  kingdom: String,
  phylum: String,
  class: String,
  order: String,
  family: String,
  genus: String,
  // Optional: Additional details
  habitat: String,
  edibility: String, // Edible, poisonous, etc.
  distribution: String,
  // Optional: Links for further information
  wikipediaUrl: String,
  mushroomObserverUrl: String,

  // Add a field to store user favorites
  favorites: [{
    userId: { 
      type: mongoose.Schema.Types.ObjectId,
      ref: 'User',
      required: true
    },
    favoritedAt: {
      type: Date,
      default: Date.now
    }
  }],
  
  // Add a field for region data
  region: {
    type: String, 
  }
});

const Mushroom = mongoose.model('Mushroom', MushroomSchema);

module.exports = Mushroom; 
