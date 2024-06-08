// backend/models/ImageObservation.js
const mongoose = require('mongoose');
const Schema = mongoose.Schema;

const imageObservationSchema = new mongoose.Schema({
  image: { type: Schema.Types.ObjectId, ref: 'Image', required: true },
  observation: { type: Schema.Types.ObjectId, ref: 'Observation', required: true } 
});

// Unique compound index to prevent duplicate image-observation pairs
imageObservationSchema.index({ image: 1, observation: 1 }, { unique: true });

const ImageObservation = mongoose.model('ImageObservation', imageObservationSchema);

module.exports = ImageObservation;

