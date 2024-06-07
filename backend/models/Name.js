// backend/models/Name.js
const mongoose = require('mongoose');

const nameSchema = new mongoose.Schema({
  id: { type: Number, required: true, unique: true },
  text_name: { type: String, required: true },
  author: { type: String, required: true },
  deprecated: { type: Boolean, required: true },
  correct_spelling_id: { type: Number },
  synonym_id: { type: Number },
  rank: { type: Number, required: true },
  observations: [{ type: mongoose.Schema.Types.ObjectId, ref: 'Observation' }],
  descriptions: [{ type: mongoose.Schema.Types.ObjectId, ref: 'NameDescription' }],
  classifications: [{ type: mongoose.Schema.Types.ObjectId, ref: 'NameClassification' }],
});

// Create a compound index for efficient lookups
nameSchema.index({ correct_spelling_id: 1, synonym_id: 1 });

const Name = mongoose.model('Name', nameSchema);

module.exports = Name;

// Blocker:  "The 2nd parameter to mongoose.model() should be a schema or a POJO" 
//  - Error persists despite trying various solutions, including explicit creation and different import approaches.
//  - Checked for typos in schema imports and model creation in index.js.
