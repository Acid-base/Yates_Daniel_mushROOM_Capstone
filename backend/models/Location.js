// backend/models/Location.js
const mongoose = require('mongoose'); // Import mongoose at the top 
const locationSchema = new mongoose.Schema({
  id: { type: Number, required: true, unique: true },
  name: { type: String, required: true },
  // Use GeoJSON Polygon for area definition
  area: {
    type: {
      type: String,
      enum: ['Polygon'],
      required: true
    },
    coordinates: {
      type: [[[Number]]],
      required: true
    }
  },
  high: { type: Number },
  low: { type: Number },
  observations: [{ type: mongoose.Schema.Types.ObjectId, ref: 'Observation' }],
  descriptions: [{ type: mongoose.Schema.Types.ObjectId, ref: 'LocationDescription' }],
});

// Create indexes for efficient querying
locationSchema.index({ id: 1 });
locationSchema.index({ "area": "2dsphere" }); // GeoSpatial index

const Location = mongoose.model('Location', locationSchema);

module.exports = Location;