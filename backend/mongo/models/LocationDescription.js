// backend/models/LocationDescription.js
const mongoose = require('mongoose'); 
const Schema = mongoose.Schema;

const locationDescriptionSchema = new mongoose.Schema({
  // id: { type: Number, required: true, unique: true }, // Removed: MongoDB will handle this
  location: { type: Schema.Types.ObjectId, ref: 'Location', required: true },
  source_type: { type: String, required: true },
  source_name: { type: String },
  gen_desc: { type: String },
  ecology: { type: String },
  species: { type: String },
  notes: { type: String },
  refs: { type: String }
});

locationDescriptionSchema.index({ location: 1 }); 
locationDescriptionSchema.index({ source_type: 1 });
locationDescriptionSchema.index({ // Text index for multiple fields
  "gen_desc": "text", 
  "ecology": "text", 
  "species": "text", 
  "notes": "text", 
  "refs": "text" 
}); 
const LocationDescription = mongoose.model('LocationDescription', locationDescriptionSchema);

module.exports = LocationDescription;
