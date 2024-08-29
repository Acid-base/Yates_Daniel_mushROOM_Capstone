// backend/src/controllers/favoriteController.ts
import { Request, Response } from 'express';
import {
  createFavorite,
  getFavoritesByUser,
  hasFavorited,
  deleteFavorite,
} from '../data/favoriteService';

// Create a new favorite
export const createFavoriteController = async (req: Request, res: Response) => {
  try {
    const { userId, mushroomId } = req.body;

    // Check if favorite already exists
    const favoriteExists = await hasFavorited(userId, mushroomId);
    if (favoriteExists) {
      return res.status(400).json({ error: 'Mushroom is already favorited' });
    }

    // Create new favorite
    const newFavorite = await createFavorite({ userId, mushroomId });

    // Send success response
    res.status(201).json(newFavorite);
  } catch (error) {
    res.status(500).json({ error: 'Failed to create favorite' });
  }
};

// Get all favorites for a user
export const getFavoritesByUserController = async (req: Request, res: Response) => {
  try {
    const favorites = await getFavoritesByUser(req.params.userId);
    res.status(200).json(favorites);
  } catch (error) {
    res.status(500).json({ error: 'Failed to get favorites' });
  }
};

// Check if a user has favorited a mushroom
export const hasFavoritedController = async (req: Request, res: Response) => {
  try {
    const { userId, mushroomId } = req.params;

    const hasFavorited = await hasFavorited(userId, mushroomId);

    res.status(200).json({ favorited: hasFavorited });
  } catch (error) {
    res.status(500).json({ error: 'Failed to check favorites' });
  }
};

// Delete a favorite
export const deleteFavoriteController = async (req: Request, res: Response) => {
  try {
    const { userId, mushroomId } = req.params;

    await deleteFavorite(userId, mushroomId);

    res.status(204).send();
  } catch (error) {
    res.status(500).json({ error: 'Failed to delete favorite' });
  }
};
