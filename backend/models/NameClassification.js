const mongoose = require('mongoose');

const nameClassificationSchema = new mongoose.Schema({
  name_id: { type: Number, required: true, ref: 'Name' },
  domain: { type: String, required: true },
  kingdom: { type: String, required: true },
  phylum: { type: String, required: true },
  class: { type: String, required: true },
  order: { type: String, required: true },
  family: { type: String, required: true }
});

nameClassificationSchema.index({ name_id: 1 }, { unique: true }); // Ensure one-to-one relationship

const NameClassification = mongoose.model('NameClassification', nameClassificationSchema);

module.exports = NameClassification;
