// backend/db/index.js
const mongoose = require('mongoose');
require('dotenv').config();

const databaseUri = process.env.MONGODB_URI;

async function connectToDatabase() {
  try {
    await mongoose.connect(databaseUri, {
      useNewUrlParser: true,
      useUnifiedTopology: true
    });
    console.log('Connected to MongoDB');
  } catch (error) {
    console.error('MongoDB connection error:', error);
  }
}

module.exports = { connectToDatabase };
