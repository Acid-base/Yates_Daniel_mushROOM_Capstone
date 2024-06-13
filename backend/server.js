// server.js
import axios from 'axios';
import rateLimit from 'axios-rate-limit';
import express from 'express';
import mongoose from 'mongoose';
require('dotenv').config(); 

import cors from 'cors';
const { body, validationResult } = require('express-validator');

import { fetchAndStoreMushroomData } from './middleware/mushroomService.js'; // Import

// ... (other requires)

const app = express();
const port = process.env.PORT || 3001;
const databaseUri = process.env.MONGODB_URI

// Rate limiting (adjust as needed)
const api = rateLimit(axios.create(), { maxRequests: 1, perMilliseconds: 6000 });

// Middleware
app.use(express.json());
app.use(cors());

const scientificNames = [
  'Amanita muscaria',
  'Boletus edulis',
  'Cantharellus cibarius',
  // Add more scientific names as needed
];
// MongoDB Connection
mongoose.connect(databaseUri, {  })
  .then(() => {
    console.log('Connected to MongoDB');

    // Fetch and store mushroom data for the specified scientific names
    fetchAndStoreMushroomData(scientificNames)
      .then(() => {
        console.log('Mushroom data fetching and storing completed.');
      })
      .catch((error) => {
        console.error('Error:', error);
      });
  })
  .catch((error) => {
    console.error('MongoDB connection error:', error); 
  });

// ... (rest of server.js)
