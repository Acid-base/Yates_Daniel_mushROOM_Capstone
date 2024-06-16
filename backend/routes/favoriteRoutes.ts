// backend/routes/favoriteRoutes.ts
// This file defines routes related to favorites

import express, { Request, Response } from 'express';
import Mushroom from '../models/MushroomModel';

const router = express.Router();

// Example: Get all favorite mushrooms for a user
// Assuming you have a way to identify users (e.g., authentication middleware)
router.get('/user/:userId', async (req: Request, res: Response) => {
  try {
    const userId = req.params.userId; 
    const favoriteMushrooms = await Mushroom.find({ 
      // Example: Assuming a 'favorites' array field in the User model
      // Replace with your actual logic for associating favorites with users
      _id: { $in: userId.favorites } 
    });

    res.json(favoriteMushrooms);
  } catch (error) {
    console.error('Error fetching favorite mushrooms:', error);
    res.status(500).json({ message: 'Internal server error' });
  }
});

// Add more favorite-related routes (e.g., add, remove, update)

export default router;
