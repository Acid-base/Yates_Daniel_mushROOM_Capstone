// backend/models/Mushroom.js
const mongoose = require('mongoose');

const mushroomSchema = new mongoose.Schema({
  id: { type: Number, required: true, unique: true }, // Assuming your CSV has an ID column
  name: { type: String, required: true },
  scientific_name: { type: String, required: true },
  when: { type: Date }, // Date of observation
  lat: { type: Number },
  lng: { type: Number },
  where: { type: String },
  user_id: { type: Number }, // ID of the user who made the observation
  thumb_image_id: { type: Number, ref: 'Image' },  // ID of the thumbnail image 
  // Fields from the MushroomObserver database schema
  family: { type: String },
  genus: { type: String },
  type: {
    type: String,
    enum: ['Edible', 'Poisonous', 'Unknown'],
    default: 'Unknown'
  },
  // Additional fields based on your needs
  observations: [{ type: mongoose.Schema.Types.ObjectId, ref: 'Observation' }], // Reference to Observation
  descriptions: [{ type: mongoose.Schema.Types.ObjectId, ref: 'NameDescription' }], // Reference to NameDescription
  classifications: [{ type: mongoose.Schema.Types.ObjectId, ref: 'NameClassification' }], // Reference to NameClassification 
});

// Create an index for searching by name 
mushroomSchema.index({ name: "text", scientific_name: "text" }); 

const Mushroom = mongoose.model('Mushroom', mushroomSchema);

module.exports = Mushroom;

