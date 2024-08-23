// server.js
const express = require('express');
const mongoose = require('mongoose');
const axios = require('axios');
const rateLimit = require('axios-rate-limit');
const { APIError, DatabaseError } = require('./middleware/customErrors');
const Mushroom = require('./models/MushroomModel');
const User = require('./models/UserModel');
const BlogPost = require('./models/BlogPostModel');

const logger = require('./middleware/logger');
const authenticateToken = require('./middleware/auth');
const userRoutes = require('./routes/UserRoutes');
const mushroomRouter = require('./routes/MushroomRoutes'); 
const cacheManager = require('./data/cacheManager.js');
const blogRouter = require('./routes/BlogRoutes');
const blogController = require('./controllers/blogController');
const db = require('./data/db'); 
const mushroomService = require('./data/db'); // Import from db.js
// Removed the fetchDataFromAPI and fetchAndStoreMushroomData functions from here 
// require('dotenv').config();

const cors = require('cors');
const { body, validationResult } = require('express-validator'); 

const app = express();
const port = 3001;
// Removed the fetchDataFromAPI and fetchAndStoreMushroomData functions from here 
app.listen(port, async () => {
  try {
    await db.connectToDatabase();
    console.log(`Mushroom Explorer backend listening at http://localhost:${port}`);

    // Call fetchAndStoreMushroomData 
    await mushroomService.fetchAndStoreMushroomData(); 
  } catch (error) {
    console.error('Error starting the server:', error); 
  }
});
