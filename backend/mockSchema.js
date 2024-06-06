// models/Mushroom.js - Defines the MongoDB schema for mushroom data 

const mongoose = require('mongoose');

// Create a new Mongoose schema - This defines the structure of your data
const mushroomSchema = new mongoose.Schema({
  commonName: { type: String, required: true }, // Common name is a required string
  scientificName: { type: String, required: true }, // Scientific name is a required string
  imageUrl: { type: String }, // You can store image URLs as strings
  edibility: { type: String }, // Edibility is a string (e.g., "Edible", "Poisonous") 
  habitat: { type: String }, // Habitat description as a string
  // ... add other relevant fields as needed
});

// Create a Mongoose model based on the schema 
// This allows you to interact with the 'mushrooms' collection in your MongoDB database
const Mushroom = mongoose.model('Mushroom', mushroomSchema); 

// Export the Mushroom model so you can use it in other parts of your backend
module.exports = Mushroom; 
