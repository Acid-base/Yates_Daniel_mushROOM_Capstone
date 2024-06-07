// backend/models/ImageObservation.js
const mongoose = require('mongoose');

const imageObservationSchema = new mongoose.Schema({
  image_id: { type: Number, required: true, ref: 'Image' }, // Use Number for referencing
  observation_id: { type: Number, required: true, ref: 'Observation' }, // Use Number for referencing
});

imageObservationSchema.index({ image_id: 1 });
imageObservationSchema.index({ observation_id: 1 });

const ImageObservation = mongoose.model('ImageObservation', imageObservationSchema);

module.exports = ImageObservation;
