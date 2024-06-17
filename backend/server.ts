// backend/server.ts
// This file initializes our Express app and configures middleware

// Import necessary modules
import express, { Application, ErrorRequestHandler, NextFunction, Request, Response } from 'express';
import cors from 'cors';
import rateLimit from 'express-rate-limit';
import favoriteRoutes from './routes/favoriteRoutes'; 
import axios from 'axios'; 
import retry from 'async-retry'; 
import logger from './middleware/logger'; 
import Mushroom from './models/MushroomModel'; // Import Mushroom model - should be PascalCase
import mongoose from 'mongoose';
import 'dotenv/config'

// Create Express app
const app: Application = express();
const PORT = process.env.PORT || 5000;

// Middleware
app.use(cors());  // Enable CORS for all origins
app.use(express.json()); // Middleware for parsing JSON bodies
app.use(logger); // Custom logger middleware (assuming you have it defined)

// Rate limiting middleware
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // Limit each IP to 100 requests per windowMs
  legacyHeaders: false, // Disable legacy rate limit headers
  // Custom error handler
  handler: (req: Request, res: Response) => {
    res.status(429).json({ message: 'Too Many Requests. Please try again later.' });
  },
});
app.use(limiter); 

// API Routes
app.use('/api/favorites', favoriteRoutes);

// Error Handling Middleware
// This should be placed after all other app.use() and routes calls
app.use(((err: Error, req: Request, res: Response, next: NextFunction) => {
  console.error(err.stack);
  res.status(500).json({ message: 'Internal Server Error' });
}) as ErrorRequestHandler);


// Connect to MongoDB and Start Server
async function startServer() {
  try {
    await mongoose.connect(process.env.MONGODB_URI || '');
    console.log('Connected to MongoDB'); 

    app.listen(PORT, () => {
      console.log(`Server listening on port ${PORT}`);
    });
  } catch (error) {
    console.error('Error connecting to MongoDB or starting the server:', error);
  }
}

startServer();
