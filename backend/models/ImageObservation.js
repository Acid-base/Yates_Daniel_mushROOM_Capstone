// backend/models/ImageObservation.js
const mongoose = require('mongoose');

const imageObservationSchema = new mongoose.Schema({
  image_id: { type: Number, required: true, ref: 'Image' }, 
  observation_id: { type: Number, required: true, ref: 'Observation' }, 
});

imageObservationSchema.index({ image_id: 1 });
imageObservationSchema.index({ observation_id: 1 });

const ImageObservation = mongoose.model('ImageObservation', imageObservationSchema);

module.exports = ImageObservation;

// Blocker:  "The 2nd parameter to mongoose.model() should be a schema or a POJO" 
//  - Error persists despite trying various solutions, including explicit creation and different import approaches.
//  - Checked for typos in schema imports and model creation in index.js.
