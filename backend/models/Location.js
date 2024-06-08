// backend/models/Location.js
const mongoose = require('mongoose'); 

const locationSchema = new mongoose.Schema({
  // id: { type: Number, required: true, unique: true }, // Removed: MongoDB can auto-generate _id
  name: { type: String, required: true },
  area: {
    type: {
      type: String,
      enum: ['Polygon'], // Only Polygons for now, consider adding more later if needed
      required: true
    },
    coordinates: {
      type: [[[Number]]], // Array of polygons (for complex shapes)
      required: true
    }
  },
  high: { type: Number }, 
  low: { type: Number } 
});

// Create indexes for efficient querying
locationSchema.index({ name: 1 }); // Index for searching by name
locationSchema.index({ "area": "2dsphere" }); // Geospatial index

const Location = mongoose.model('Location', locationSchema);

module.exports = Location;

