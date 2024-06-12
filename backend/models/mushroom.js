// models/mushroom.js 
const mongoose = require('mongoose');

const MushroomSchema = new mongoose.Schema({
  // Basic Information
  scientificName: { type: String, required: true, unique: true }, // Unique scientific name
  commonName: { type: String, required: true },
  // Taxonomy
  kingdom: String,
  phylum: String,
  class: String,
  order: String,
  family: String,
  genus: String,
  // Description (can be more detailed if needed)
  description: String,
  // Image Information
  imageUrl: { type: String, required: true }, // Primary image URL
  additionalImages: [String], // Array to store additional image URLs 
  // Optional: Additional details
  habitat: String,
  edibility: String, // Edible, poisonous, etc.
  distribution: String,
  // Optional: Links for further information
  wikipediaUrl: String,
  mushroomObserverUrl: String 
});

const Mushroom = mongoose.model('Mushroom', MushroomSchema);

module.exports = Mushroom; 
