// backend/models/Observation.js
const mongoose = require('mongoose');   

const observationSchema = new mongoose.Schema({
  id: { type: Number, required: true, unique: true },
  name_id: { type: Number, required: true, ref: 'Name' },
  when: { type: Date, required: true },
  location_id: { type: Number, required: true, ref: 'Location' },
  // Use GeoJSON Point for location data
  location: {
    type: {
      type: String,
      enum: ['Point'],
      required: true
    },
    coordinates: {
      type: [Number],
      required: true
    }
  },
  alt: { type: Number },
  vote_cache: { type: Number },
  is_collection_location: { type: Boolean, required: true },
  thumb_image_id: { type: Number, ref: 'Image' },
  // Remove thumb_image_id
  image: [{ type: mongoose.Schema.Types.ObjectId, ref: 'Image' }],  // Add array of references to Images
});

// Create indexes for efficient querying
observationSchema.index({ name_id: 1 });
observationSchema.index({ when: 1 });
observationSchema.index({ location_id: 1 });
observationSchema.index({ "location": "2dsphere" }); // GeoSpatial index

const Observation = mongoose.model('Observation', observationSchema);

module.exports = Observation;

// Blocker:  "The 2nd parameter to mongoose.model() should be a schema or a POJO" 
//  - Error persists despite trying various solutions, including explicit creation and different import approaches.
//  - Checked for typos in schema imports and model creation in index.js.
