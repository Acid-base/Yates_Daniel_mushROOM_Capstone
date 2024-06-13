// db.js
const mongoose = require('mongoose');
const axios = require('axios'); // Assuming you are using axios for fetching data
const { DatabaseError } = require('../middleware/customErrors');
const Mushroom = require('../models/MushroomModel'); // Assuming you have a Mushroom model
require('dotenv').config();
const databaseUri = process.env.MONGODB_URI;

let connection; 

async function connectToDatabase() {
  try {
    connection = await mongoose.connect(databaseUri, {
      // ... your mongoose connection options
    });
    console.log('Connected to MongoDB');
    return connection;
  } catch (error) {
    throw new DatabaseError(`MongoDB connection error: ${error.message}`);
  }
}

async function disconnectFromDatabase() {
  try {
    if (connection) {
      await connection.close();
      console.log('Disconnected from MongoDB');
    }
  } catch (error) {
    console.error('Error disconnecting from MongoDB:', error);
  }
}

// Add MongoDB data seeding function
const fetchAndStoreMushroomData = async () => {
  try {
    const mushrooms = await axios.get('https://example.com/api/mushrooms'); // Replace with your actual API
    await Mushroom.insertMany(mushrooms.data);
    console.log('Mushroom data fetched and stored successfully.');
  } catch (error) {
    console.error('Error fetching and storing mushroom data:', error);
  }
};

module.exports = { 
  connectToDatabase, 
  disconnectFromDatabase, 
  fetchAndStoreMushroomData 
};
