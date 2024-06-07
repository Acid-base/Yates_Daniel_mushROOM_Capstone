const mongoose = require('mongoose'); // Import mongoose at the top 

const locationDescriptionSchema = new mongoose.Schema({
  id: { type: Number, required: true, unique: true },
  location_id: { type: Number, required: true, ref: 'Location' },
  source_type: { type: String, required: true },
  source_name: { type: String },
  gen_desc: { type: String },
  ecology: { type: String },
  species: { type: String },
  notes: { type: String },
  refs: { type: String },
});

locationDescriptionSchema.index({ location_id: 1 });
locationDescriptionSchema.index({ source_type: 1 });
locationDescriptionSchema.index({ "gen_desc": "text", "ecology": "text", "species": "text", "notes": "text", "refs": "text" }); // Text index for searching

const LocationDescription = mongoose.model('LocationDescription', locationDescriptionSchema);

module.exports = LocationDescription;
