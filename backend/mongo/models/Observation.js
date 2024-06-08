// backend/models/Observation.js
const mongoose = require('mongoose');

const observationSchema = new mongoose.Schema({
  //id: { type: Number, required: true, unique: true }, // Removed: MongoDB will handle _id
  name: { type: mongoose.Schema.Types.ObjectId, ref: 'Name', required: true },
  when: { type: Date, required: true },
  location: { type: mongoose.Schema.Types.ObjectId, ref: 'Location', required: true },
  // Using GeoJSON Point directly within location 
  locationPoint: { 
    type: {
      type: String,
      enum: ['Point'],
      required: true
    },
    coordinates: {
      type: [Number], // [Longitude, Latitude]
      required: true
    }
  },
  alt: { type: Number },
  vote_cache: { type: Number },
  is_collection_location: { type: Boolean, required: true },
  //thumb_image_id: { type: Number, ref: 'Image' }, // Removed: Using images array now
  images: [{ type: mongoose.Schema.Types.ObjectId, ref: 'Image' }] // Array of image references 
});

// Create indexes for efficient querying
observationSchema.index({ name: 1 });
observationSchema.index({ when: 1 });
observationSchema.index({ location: 1 });
observationSchema.index({ "locationPoint": "2dsphere" }); // GeoSpatial index

const Observation = mongoose.model('Observation', observationSchema);

module.exports = Observation;
