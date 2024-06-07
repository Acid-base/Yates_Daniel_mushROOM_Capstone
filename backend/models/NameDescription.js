// backend/models/NameDescription.js
const mongoose = require('mongoose');

const nameDescriptionSchema = new mongoose.Schema({
  id: { type: Number, required: true, unique: true },
  name_id: { type: Number, required: true, ref: 'Name' },
  source_type: { type: String, required: true },
  source_name: { type: String },
  general_description: { type: String },
  diagnostic_description: { type: String },
  distribution: { type: String },
  habitat: { type: String },
  look_alikes: { type: String },
  uses: { type: String },
  notes: { type: String },
  refs: { type: String }
});

nameDescriptionSchema.index({ name_id: 1 });
nameDescriptionSchema.index({ source_type: 1 });
nameDescriptionSchema.index({ "general_description": "text", "diagnostic_description": "text", "distribution": "text", "habitat": "text", "look_alikes": "text", "uses": "text", "notes": "text", "refs": "text" }); // Text index for searching

const NameDescription = mongoose.model('NameDescription', nameDescriptionSchema);

module.exports = NameDescription;

// Blocker:  "The 2nd parameter to mongoose.model() should be a schema or a POJO" 
//  - Error persists despite trying various solutions, including explicit creation and different import approaches.
//  - Checked for typos in schema imports and model creation in index.js.
