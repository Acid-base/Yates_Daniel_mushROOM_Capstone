import express from 'express';
import rateLimit from 'express-rate-limit';
import mongoose from './mongo/db';
import { fetchObservationImages, fetchObservationDetails, fetchMushroomNames } from './utils/apiRequests';
import { storeObservations, storeImages, storeNames } from './utils/dataStorage';
import mapObservation from './utils/dataMapper';

const app = express();
const PORT = process.env.PORT || 5000;

// Rate Limiting
const apiLimiter = rateLimit({
  windowMs: 1 * 60 * 1000,
  max: 15, 
  message: { error: 'Too many requests, please try again later.' },
});

// API Routes

// 1. Get All Observations (with Pagination)
app.get('/api/observations', apiLimiter, async (req, res) => {
  try {
    const page = parseInt(req.query.page) || 1;
    const limit = parseInt(req.query.limit) || 20;
    const skip = (page - 1) * limit;

    const observations = await Observation.find()
      .skip(skip)
      .limit(limit)
      .lean(); // Use lean() for plain JavaScript objects

    const totalObservations = await Observation.countDocuments();

    res.json({ 
      observations, 
      currentPage: page, 
      totalPages: Math.ceil(totalObservations / limit) 
    });
  } catch (error) {
    console.error('Error fetching observations:', error);
    res.status(500).json({ error: 'Failed to fetch observations' });
  }
});

// 2. Get Observation Details by ID
app.get('/api/observations/:id', apiLimiter, async (req, res) => {
  try {
    const observationId = parseInt(req.params.id);
    const observation = await Observation.findOne({ id: observationId }).lean();

    if (!observation) {
      return res.status(404).json({ error: 'Observation not found' });
    }

    res.json(observation);
  } catch (error) {
    console.error('Error fetching observation details:', error);
    res.status(500).json({ error: 'Failed to fetch observation details' });
  }
});

// 3. Get Images for an Observation
app.get('/api/observations/:id/images', apiLimiter, async (req, res) => {
  try {
    const observationId = parseInt(req.params.id);
    const images = await Image.find({ observationId }).lean(); 

    res.json(images);
  } catch (error) {
    console.error('Error fetching images:', error);
    res.status(500).json({ error: 'Failed to fetch images' });
  }
});

// 4. Search Observations by Name
app.get('/api/search/observations', apiLimiter, async (req, res) => {
  try {
    const searchTerm = req.query.q;

    if (!searchTerm) {
      return res.status(400).json({ error: 'Missing search term' });
    }

    // Adjust the search logic based on your requirements (e.g., case-insensitive search)
    const observations = await Observation.find({ 
      name: { $regex: new RegExp(searchTerm, 'i') } // Case-insensitive regex search
    }).lean(); 

    res.json(observations);
  } catch (error) {
    console.error('Error searching observations:', error);
    res.status(500).json({ error: 'Failed to search observations' });
  }
});

// 5. Get Mushroom Names (with Pagination)
app.get('/api/names', apiLimiter, async (req, res) => {
  try {
    const page = parseInt(req.query.page) || 1;
    const limit = parseInt(req.query.limit) || 20;
    const skip = (page - 1) * limit;

    const names = await Name.find()
      .skip(skip)
      .limit(limit)
      .lean();

    const totalNames = await Name.countDocuments();

    res.json({ 
      names, 
      currentPage: page, 
      totalPages: Math.ceil(totalNames / limit) 
    });
  } catch (error) {
    console.error('Error fetching names:', error);
    res.status(500).json({ error: 'Failed to fetch names' });
  }
});

// ... (Add more routes for locations, user details, advanced search, etc.)

// Start your server 
app.listen(PORT, () => console.log(`Server listening on port ${PORT}`));
