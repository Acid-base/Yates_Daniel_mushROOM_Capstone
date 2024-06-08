// backend/models/NameClassification.js
const mongoose = require('mongoose'); 
const Schema = mongoose.Schema;

const nameClassificationSchema = new mongoose.Schema({
  name: { type: Schema.Types.ObjectId, ref: 'Name', required: true, unique: true }, 
  domain: { type: String, required: true },
  kingdom: { type: String, required: true },
  phylum: { type: String, required: true },
  class: { type: String, required: true },
  order: { type: String, required: true },
  family: { type: String, required: true } 
});

//  nameClassificationSchema.index({ name: 1 }, { unique: true }); //No longer needed, unique is declared above

const NameClassification = mongoose.model('NameClassification', nameClassificationSchema);

module.exports = NameClassification;
