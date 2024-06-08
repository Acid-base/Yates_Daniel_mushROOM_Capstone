// backend/models/Name.js
const mongoose = require('mongoose'); 
const Schema = mongoose.Schema; 

const nameSchema = new Schema({
  // id: { type: Number, required: true, unique: true },  // Removed: MongoDB will handle this
  text_name: { type: String, required: true },
  author: { type: String, required: true },
  deprecated: { type: Boolean, required: true },
  correct_spelling_id: { type: Number }, 
  synonym_id: { type: Number }, 
  rank: { type: Number, required: true } 
});

// Create indexes *on the schema* 
nameSchema.index({ text_name: 1 }); // Index for the text_name field
nameSchema.index({ correct_spelling_id: 1, synonym_id: 1 }); 

const Name = mongoose.model('Name', nameSchema);

module.exports = Name;
