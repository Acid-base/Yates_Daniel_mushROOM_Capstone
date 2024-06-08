// backend/models/Image.js
const mongoose = require('mongoose');

const imageSchema = new mongoose.Schema({
  // id: { type: Number, required: true, unique: true }, // Removed: MongoDB can auto-generate _id
  content_type: { type: String, required: true },
  copyright_holder: { type: String, required: true },
  license: { type: String, required: true },
  ok_for_export: { type: Boolean, required: true },
  diagnostic: { type: Boolean, required: true },
  image_url: { type: String, required: false } 
});

// Create indexes for efficient querying
imageSchema.index({ content_type: 1 });
imageSchema.index({ copyright_holder: 1 });

const Image = mongoose.model('Image', imageSchema);

module.exports = Image;
