// backend/models/NameDescription.js
const mongoose = require('mongoose'); 
const Schema = mongoose.Schema; 

const nameDescriptionSchema = new Schema({
  // id: { type: Number, required: true, unique: true }, // Removed: MongoDB will create this
  name: { type: Schema.Types.ObjectId, ref: 'Name', required: true },
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
  // id: { type: Number, required: true } // Removed - potential conflict and not needed
});

nameDescriptionSchema.index({ name: 1 });
nameDescriptionSchema.index({ source_type: 1 });
nameDescriptionSchema.index({ 
  "general_description": "text", 
  "diagnostic_description": "text", 
  "distribution": "text", 
  "habitat": "text", 
  "look_alikes": "text", 
  "uses": "text", 
  "notes": "text", 
  "refs": "text" 
});
const NameDescription = mongoose.model('NameDescription', nameDescriptionSchema);

module.exports = NameDescription;
