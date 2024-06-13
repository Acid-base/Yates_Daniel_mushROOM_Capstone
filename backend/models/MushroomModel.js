// MushroomModel.js 
import mongoose from 'mongoose';

const MushroomSchema = new mongoose.Schema({
  scientificName: { type: String, required: true, unique: true }, 
  latitude: { type: Number, required: true },
  longitude: { type: Number, required: true },
  imageUrl: String, // Primary image URL
  description: String, 
  commonName: String,
  family: String,
  genus: String,
  region: {
    type: String,
  },
  gallery: [{ 
    url: String, // Full-size image URL
    thumbnailUrl: String // Thumbnail image URL
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
  }] 
});

const Mushroom = mongoose.model('Mushroom', MushroomSchema);

export default MushroomModel; 


