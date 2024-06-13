// mushroom.js 
import mongoose from 'mongoose';

const MushroomSchema = new mongoose.Schema({
  scientificName: { type: String, required: true, unique: true }, 
  latitude: { type: Number, required: true },
  longitude: { type: Number, required: true },
  imageUrl: String,
  description: String,
  commonName: String,
  family: String,
  genus: String,
  favorites: [
    {
      userId: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'User',
      required: true
    },
    favoritedAt: {
      type: Date,
      default: Date.now
    }
    }
  ],
  region: {
    type: String,
  },
  // ... other relevant fields
  // Basic Information 
  // Location 
  // Image Information 
  // Description (can be more detailed if needed)
  // Taxonomy 
  // Optional: Additional details 
  // Optional: Links for further information
  // This replaces the additionalImages array with a gallery structure
  gallery: [{
    url: String,
    thumbnailUrl: String
  }], 
  kingdom: String,
  phylum: String,
  class: String,
  order: String,
  habitat: String,
  edibility: String, // Edible, poisonous, etc.
  distribution: String,
  wikipediaUrl: String,
  mushroomObserverUrl: String,
});

const Mushroom = mongoose.model('Mushroom', MushroomSchema);

module.exports = Mushroom; 

